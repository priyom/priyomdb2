<?xml version="1.0"?>
<xsl:stylesheet
    version="1.0"
    xmlns="http://www.w3.org/1999/xhtml"
    xmlns:h="http://www.w3.org/1999/xhtml"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:sitemap="https://xmlns.zombofant.net/xsltea/sitemap">

  <xsl:template match="*|node()|@*">
    <xsl:copy>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates select="*|node()" />
    </xsl:copy>
  </xsl:template>

  <xsl:template name="sitemap-entry-text">
  </xsl:template>

  <xsl:template match="sitemap:entry">
    <li>
      <xsl:choose>
        <xsl:when test="@active">
          <xsl:attribute name="class">active</xsl:attribute>
          <strong><xsl:value-of select="@label" /></strong>
        </xsl:when>
        <xsl:when test="@href">
          <a href="{@href}"><xsl:value-of select="@label" /></a>
        </xsl:when>
        <xsl:otherwise>
          <span><xsl:value-of select="@label" /></span>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="sitemap:entry">
        <ul>
          <xsl:apply-templates select="sitemap:entry" />
        </ul>
      </xsl:if>
    </li>
  </xsl:template>

  <xsl:template name="sitemap">
    <xsl:param name="node" />
    <h3><xsl:value-of select="$node/@label" /></h3>
    <xsl:if test="$node/sitemap:entry">
      <ul>
        <xsl:apply-templates select="$node/sitemap:entry" />
      </ul>
    </xsl:if>
  </xsl:template>

  <xsl:template match="/h:html">
    <html>
      <head>
        <title>
          <xsl:value-of select="h:head/h:title" />
          <xsl:text> – </xsl:text>
          <xsl:text>Priyom Database Backend</xsl:text>
        </title>
        <link rel="stylesheet" href="css/core/base.min.css" type="text/css" />
        <link rel="stylesheet" href="css/screen/typography.css" type="text/css" />
        <link rel="stylesheet" href="css/navigation/hlist.css" type="text/css" />
        <link rel="stylesheet" href="css/screen/screen-FULLPAGE-layout.css" type="text/css" />
        <link rel="stylesheet" href="css/forms/gray-theme.css" type="text/css" />
        <link rel="stylesheet" href="css/style.css" type="text/css" />

        <meta name="viewport" content="width=320, initial-scale=1, user-scalable=no" />
      </head>
      <body>
        <header>
          <div class="ym-wrapper"><div class="ym-wbox">
            <h1>Priyom radio database backend</h1>
          </div></div>
        </header>
        <nav class="ym-hlist">
          <div class="ym-wrapper"><div class="ym-wbox">
            <div class="ym-grid linearize-level-1">
              <div class="ym-gl ym-g50"><div class="ym-gbox">
                <xsl:call-template name="sitemap">
                  <xsl:with-param name="node"
                                  select="h:body/h:nav/sitemap:entry[1]" />
                </xsl:call-template>
              </div></div>
              <xsl:if test="h:body/h:nav/sitemap:entry[2]">
                <div class="ym-gl ym-g25"><div class="ym-gbox">
                  <xsl:call-template name="sitemap">
                    <xsl:with-param name="node"
                                    select="h:body/h:nav/sitemap:entry[2]" />
                  </xsl:call-template>
                </div></div>
              </xsl:if>
              <xsl:if test="h:body/h:nav/sitemap:entry[3]">
                <div class="ym-gr ym-g25"><div class="ym-gbox">
                  <xsl:call-template name="sitemap">
                    <xsl:with-param name="node"
                                    select="h:body/h:nav/sitemap:entry[3]" />
                  </xsl:call-template>
                </div></div>
              </xsl:if>
            </div>
          </div></div>
        </nav>
        <xsl:apply-templates select="h:body/h:main" />
        <footer>
          <div class="ym-wrapper"><div class="ym-wbox">
            <p>A <a href="http://priyom.org">priyom.org</a> project • hacked together by Horrorcat • using <a href="http://yaml.de">yaml CSS framework</a></p>
          </div></div>
        </footer>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
