<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet
        version='1.0'
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
        xmlns:a="http://pyxwf.zombofant.net/xmlns/templates/default">
    <xsl:output method="xml" encoding="utf-8" />

    <xsl:template name="py-author-email">
        <xsl:param name="value" select="." />
        <xsl:param name="addr" select="@email" />
        <xsl:param name="tag-name" select="1" />
        <h:a property="email" href="mailto:{$addr}" content="{$addr}">
            <h:span>
                <xsl:if test="$tag-name">
                    <xsl:attribute name="property">name</xsl:attribute>
                </xsl:if>
                <xsl:value-of select="$value" />
            </h:span>
        </h:a>
    </xsl:template>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="a:sidenote">
        <h:aside class="sidenote bp-incr bp-quiet"><xsl:copy-of select="@*" /><xsl:value-of select="." /><xsl:copy-of select="./*" /></h:aside>
    </xsl:template>

    <xsl:template match="py:author">
        <h:span typeof="Person" property="author">
            <xsl:choose>
                <xsl:when test="@href">
                    <py:a property="url">
                        <xsl:attribute name="href">
                            <xsl:value-of select="href" />
                        </xsl:attribute>
                        <h:span property="name"><xsl:value-of select="." /></h:span>
                    </py:a>
                    <xsl:if test="@email">
                        <xsl:call-template name="py-author-email">
                            <xsl:with-param name="value" value="✉" />
                            <xsl:with-param name="tag-name" value="0" />
                        </xsl:call-template>
                    </xsl:if>
                </xsl:when>
                <xsl:when test="@email">
                    <xsl:call-template name="py-author-email" />
                </xsl:when>
                <xsl:otherwise>
                    <h:span property="name"><xsl:value-of select="." /></h:span>
                </xsl:otherwise>
            </xsl:choose>
        </h:span>
    </xsl:template>

    <xsl:template name="py-license-img-name">
        <xsl:param name="license" select="." />
        <xsl:choose>
            <xsl:when test="@img-href">
                <py:img>
                    <xsl:attribute name="href">
                        <xsl:value-of select="@img-href" />
                    </xsl:attribute>
                    <xsl:attribute name="title">
                        <xsl:value-of select="@name" />
                        <xsl:if test="string($license)"
                            xml:space="preserve">: <xsl:value-of select="$license" /></xsl:if>
                    </xsl:attribute>
                    <xsl:attribute name="alt">
                        <xsl:value-of select="@name" />
                    </xsl:attribute>
                </py:img>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="title"><xsl:value-of select="$license" /></xsl:attribute>
                <xsl:value-of select="@name" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="py:license">
        <xsl:choose>
            <xsl:when test="@href">
                <py:a class="license" rel="license" property="dc:license">
                    <xsl:attribute name="href"><xsl:value-of select="@href" /></xsl:attribute>
                    <xsl:call-template name="py-license-img-name" />
                </py:a>
            </xsl:when>
            <xsl:otherwise>
                <h:span class="license"><xsl:call-template name="py-license-img-name" /></h:span>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
