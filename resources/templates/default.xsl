<?xml version="1.0"?>
<xsl:stylesheet
    version="1.0"
    xmlns="http://www.w3.org/1999/xhtml"
    xmlns:h="http://www.w3.org/1999/xhtml"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="*|node()|@*">
    <xsl:copy>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates select="*|node()" />
    </xsl:copy>
  </xsl:template>

  <xsl:template match="/h:html">
    <html>
      <head>
        <title>
          <xsl:value-of select="h:head/h:title" />
          <xsl:text> – </xsl:text>
          <xsl:text>Priyom Database Backend</xsl:text>
        </title>
        <meta name="viewport" content="width=320, initial-scale=1, user-scalable=no" />
        <xsl:apply-templates select="h:head/h:link" />
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
              <xsl:apply-templates select="h:body/h:nav/*" />
            </div>
          </div></div>
        </nav>
        <main>
          <xsl:apply-templates select="h:body/h:main/@*" />
          <div class="ym-wrapper"><div class="ym-wbox">
            <xsl:apply-templates select="h:body/h:main/*" />
            <div style="clear: both;" />
          </div></div>
        </main>
        <xsl:apply-templates select="h:body/h:footer" />
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
