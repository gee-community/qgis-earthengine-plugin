---
title: Google Earth Engine Plugin for QGIS
hide:
  - navigation
  - toc
---

<style>
.md-search-result .md-typeset h1 {display:block!important; padding-top:0.65rem;}
.md-typeset .md-content__button {display:none!important;}
.md-footer__inner {display:none!important;}
.md-typeset h1, .md-typeset h2 {display:none;}
.md-typeset h5 {text-transform:none!important; color:#212529!important;}
.md-typeset h3 {font-weight:bold!important; color:#212529!important;}
</style>

<!-- CSS propios y fuentes (sug.: pásalos a extra_css en mkdocs.yml) -->
<link rel="stylesheet" href="stylesheets/qgis-plugin-earth-engine-home.css">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet" type="text/css"/>

<!-- Masthead -->
<header class="masthead">
  <div class="container"></div>
</header>

<br>

<!-- SERVICES -->
<section class="page-section" id="services">
  <div class="container">
    <div class="text-center">
      <h3 class="main_title">Google Earth Engine Plugin for QGIS</h3>
      <br>
      <p class="sub_title">
        The goal of the plugin is to make it easy for QGIS users to access data from Google Earth Engine.
        The plugin allows you to run Earth Engine Python API code in the QGIS Python Console and visualize
        the results on the QGIS Canvas. The plugin also provides a set of Processing algorithms with a
        no-code user interface to visualize and download data from Earth Engine.
      </p>

      <br>
      <hr>

      <h3 class="main_title">
        ⭐ <span id="rating-value"></span> rating votes |
        ⬇️ <span id="downloads-value"></span> downloads
        <!-- (Opcional) Última versión: <span id="latest-version"></span> -->
      </h3>

      <hr>
    </div>

    <!-- GRID DE TARJETAS -->
    <div class="row">
      <!-- Card 1 -->
      <div class="col-lg-3 col-sm-6">
        <div class="single_service mt-30 wow fadeInUpBig" data-wow-duration="1.3s" data-wow-delay="0.2s">
          <div class="service_icon">
            <a href="calcolatore_campi/field_calc/" title="Il calcolatore di campi" target="_parent">
              <i class="fas fa-calculator fa-5x"></i>
            </a>
          </div>
          <div class="service_content">
            <h4 class="service_title">
              <a href="calcolatore_campi/field_calc/" title="Il calcolatore di campi" target="_parent">Quickstart Guide</a>
            </h4>
            <p>
              <a href="calcolatore_campi/field_calc/" target="_parent">Il calcolatore di campi</a> consente di eseguire calcoli
              sulla base di valori di attributo esistenti o funzioni definite (area, lunghezza, buffer, ecc.).
              I risultati possono essere scritti in un nuovo campo, un campo virtuale o aggiornare un campo esistente.
            </p>
          </div>
        </div>
      </div>

      <!-- Card 2 -->
      <div class="col-lg-3 col-sm-6">
        <div class="single_service mt-30 wow fadeInUpBig" data-wow-duration="1.3s" data-wow-delay="0.5s">
          <div class="service_icon">
            <a href="gr_funzioni/gruppo_funzioni/" title="Elenco funzioni QGIS" target="_parent">
              <i class="fas fa-plus fa-5x"></i>
            </a>
          </div>
          <div class="service_content">
            <h4 class="service_title">
              <a href="gr_funzioni/gruppo_funzioni/" title="Elenco funzioni QGIS" target="_parent">Installation</a>
            </h4>
            <p>
              Guida con esempi e screenshot per usare il calcolatore di campi.
              Nella sezione <a href="esempi/lista_esempi/" target="_parent">ESERCIZI</a> trovi esercizi step-by-step.
            </p>
          </div>
        </div>
      </div>

      <!-- Card 3 -->
      <div class="col-lg-3 col-sm-6">
        <div class="single_service mt-30 wow fadeInUpBig" data-wow-duration="1.3s" data-wow-delay="0.8s">
          <div class="service_icon">
            <a href="corso_formazione/corso_di_formazione/" title="Corso di formazione (Novità)" target="_parent">
              <i class="fas fa-user-graduate fa-5x"></i>
            </a>
          </div>
          <div class="service_content">
            <h4 class="service_title">
              <a href="corso_formazione/corso_di_formazione/" title="Corso di formazione (Novità)" target="_parent">
                Using Earth Engine in QGIS
              </a>
            </h4>
            <p>
              Corso per utenti QGIS che vogliono approfondire tabella attributi e calcolatore di campi.
              Durata minima 16 ore (preferibilmente 2×8h). <a href="corso_formazione/corso_di_formazione/" target="_parent">Programma…</a>
            </p>
          </div>
        </div>
      </div>

      <!-- Card 4 -->
      <div class="col-lg-3 col-sm-6">
        <div class="single_service mt-30 wow fadeInUpBig" data-wow-duration="1.3s" data-wow-delay="1.1s">
          <div class="service_icon">
            <a href="contributing/" title="Supporter" target="_parent">
              <i class="fas fa-user-plus fa-5x"></i>
            </a>
          </div>
          <div class="service_content">
            <h4 class="service_title">
              <a href="contributing/" title="Supporter" target="_parent">Tutorials</a>
            </h4>
            <p>
              Puoi contribuire a <strong>HfcQGIS</strong> con donazioni, segnalazione di bug, suggerimenti, pull request,
              o documentando funzioni. <a href="contributing/#donazione" target="_parent">Scopri come</a>.
            </p>
          </div>
        </div>
      </div>
    </div><!-- /row -->
  </div><!-- /container -->
</section>

<!-- LA GUIDA -->
<section class="page-section" id="guide">
  <div class="container">
    <div class="row align-items-center justify-content-center justify-content-lg-between">
      <div class="col-lg-12">
        <div class="header_hero_content mt-45">
          <br><hr><br>
          <h4 class="service_title">La guida</h4>
          <p class="wow fadeInUp" data-wow-duration="1.3s" data-wow-delay="1.1s">
            Questa guida NON sostituisce il
            <a href="https://qgis.org/it/docs/index.html#" target="_blank">manuale</a> online di QGIS: aiuta a comprenderlo.
            Versione <a href="https://squidfunk.github.io/mkdocs-material/" target="_blank">MkDocs</a> del lavoro di Salvatore FIANDACA,
            realizzata dalla comunità <a href="https://hfcqgis-md.readthedocs.io/it/latest/ods/" target="_blank"><strong>OpenDataSicilia</strong></a>:
            <a href="https://twitter.com/aborruso" target="_blank">Andrea Borruso</a>,
            <a href="https://twitter.com/totofiandaca" target="_blank">Totò Fiandaca</a>,
            <a href="https://twitter.com/gbvitrano" target="_blank">Giovan Battista Vitrano</a>,
            usando il tema <a href="https://squidfunk.github.io/mkdocs-material/" target="_blank" rel="noopener">Material for MkDocs</a>.
          </p>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- JS para actualizar métricas -->
<script src="static/js/load_data.js"></script>
