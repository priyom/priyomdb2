import functools

import teapot.routing.selectors

__all__ = [
    "paginate"]

class paginate(teapot.routing.selectors.Selector):
    @staticmethod
    def _default_queryfunc(objcls, dbsession):
        return dbsession.query(objcls)

    def __init__(self,
                 objcls,
                 items_per_page,
                 defaultorder,
                 destarg,
                 queryfunc=None,
                 pagearg="page",
                 orderbyarg="order_by",
                 orderdirarg="d",
                 **kwargs):
        super().__init__(**kwargs)
        self._objcls = objcls
        self._items_per_page = items_per_page
        self._pagearg = pagearg
        self._orderbyarg = orderbyarg
        self._orderdirarg = orderdirarg
        self._destarg = destarg
        self._queryfunc = queryfunc or functools.partial(
            self._default_queryfunc, objcls)

        # fail early
        self._orderby_field, self._orderby_dir = defaultorder
        if isinstance(self._orderby_field, str):
            self._orderby_field = getattr(self._objcls, self._orderby_field)

    def select(self, request):
        data = request.query_data

        try:
            page = int(data.get(self._pagearg, []).pop())
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        try:
            orderby_field_arg = data.get(self._orderbyarg, []).pop()
            orderby_field = getattr(self._objcls, orderby_field_arg)
        except (ValueError, AttributeError):
            orderby_field = self._orderby_field
            orderby_dir = self._orderby_dir
        else:
            try:
                orderby_dir_arg = data.get(self._orderdirarg, []).pop()
                orderby_dir = "desc" if orderby_dir_arg == "desc" else "asc"
            except ValueError:
                orderby_dir = self._orderby_dir

        request.kwargs[self._destarg] = Page(
            self._queryfunc(request.original_request.dbsession),
            self._objcls,
            page,
            self._items_per_page,
            orderby_field,
            orderby_dir)

        return True

    def unselect(self, request):
        try:
            arg = request.kwargs.pop(self._destarg)
        except KeyError:
            arg = 1

        if not isinstance(arg, Page):
            try:
                arg = int(arg)
            except ValueError:
                raise ValueError("pagination selector expects page number or "
                                 "Page object for unrouting")

            if arg <= 0:
                raise ValueError("page numbers start at 1")

            page = Page(
                self._queryfunc(request.original_request.dbsession),
                self._objcls,
                arg,
                self._items_per_page,
                self._orderby_field,
                self._orderby_dir)
        else:
            page = arg

        request.query_data[self._pagearg] = [str(page.page)]
        field, direction = page.order_by
        request.query_data[self._orderbyarg] = [field.name]
        request.query_data[self._orderdirarg] = [direction]


class Page:
    def __init__(self,
                 query,
                 objcls,
                 page,
                 items_per_page,
                 orderby_field,
                 orderby_dir):
        self._base_query = query
        self._objcls = objcls

        total = query.count()
        self.total_pages = (total+(items_per_page-1)) // items_per_page

        query = query.order_by(getattr(orderby_field, orderby_dir)())
        offset = (page-1) * items_per_page
        if total < offset:
            offset = (self.total_pages-1)*items_per_page

        query = query.offset(offset).limit(items_per_page)

        self.order_by = (orderby_field, orderby_dir)
        self.page = page
        self.items_per_page = items_per_page
        self.query = query
        self.length = min(total - offset, items_per_page)

    def __iter__(self):
        return iter(self.query)

    def __len__(self):
        return self.length

    def at_page(self, page):
        return type(self)(
            self._base_query,
            self._objcls,
            page,
            self.items_per_page,
            *self.order_by)

    def with_order_by_field(self, field):
        return type(self)(
            self._base_query,
            self._objcls,
            self.page,
            self.items_per_page,
            getattr(self._objcls, field),
            self.order_by[1])

    def with_order_by_direction(self, direction):
        return type(self)(
            self._base_query,
            self._objcls,
            self.page,
            self.items_per_page,
            self.order_by[0],
            direction)
