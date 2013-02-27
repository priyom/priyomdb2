<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet
        version='1.0'
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
        xmlns:a="http://pyxwf.zombofant.net/xmlns/templates/default">
    <xsl:import href="final-lib.xsl" />

    <xsl:output method="xml" encoding="utf-8" />

    <xsl:template match="h:body" xmlns="http://www.w3.org/1999/xhtml">
        <!-- <nav class="bread">You are here: <py:crumb id="bread" /></nav> -->
        <a id="content" />
        <div>
            <xsl:copy-of select="./@*" />
            <xsl:apply-templates select="./*" />
        </div>
    </xsl:template>

    <xsl:template match="py:page">
        <py:page>
            <py:meta>
                <!-- <h:base href="{$url_scheme}://{$host_name}{$url_root}/" /> -->
                <py:title><xsl:value-of select="$doc_title" /> • <xsl:value-of select="$site_title" /></py:title>
                <xsl:copy-of select="py:meta/py:link" />
                <xsl:copy-of select="py:meta/py:kw" />
                <xsl:copy-of select="py:meta/h:meta" />
                <py:link rel="shortcut icon" href="img/favicon.ico" />
                <h:meta name="title" content="{$doc_title}" />
                <xsl:if test="py:meta/py:description">
                    <h:meta name="description" content="{py:meta/py:description}" />
                </xsl:if>
                <py:link rel="apple-touch-icon" href="img/apple-touch-57x57.png" />
            </py:meta>
            <body xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en" vocab="http://schema.org/">
                <section>
                   <header>
                       <h1><xsl:value-of select="$site_title" /></h1>
                   </header>
                   <xsl:apply-templates select="h:body" />
                </section>
            </body>
        </py:page>
    </xsl:template>
</xsl:stylesheet>
