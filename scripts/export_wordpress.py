#!/usr/bin/env python3
"""
Convert RTMS Scanner Architecture documentation into self-contained, 
styled HTML snippets ready for copy-pasting into WordPress Gutenberg 
(Custom HTML Block / Bloc HTML personnalisé).
"""

import os
import re
import markdown

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(PROJECT_DIR, "docs-client", "solution")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "exports", "wordpress")

# Modern, scoped CSS that adapts gracefully to any WordPress theme
SCOPED_CSS = """
<style>
.rtms-wp-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    line-height: 1.65;
    font-size: 16px;
    max-width: 1000px;
    margin: 0 auto;
    padding: 10px;
}
.rtms-wp-container * {
    box-sizing: border-box;
}
.rtms-wp-container h1 {
    font-size: 2.2rem;
    font-weight: 800;
    color: #0f172a;
    margin-top: 0;
    margin-bottom: 1rem;
    line-height: 1.25;
    background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.rtms-wp-container h2 {
    font-size: 1.55rem;
    font-weight: 700;
    color: #1e293b;
    margin-top: 2.5rem;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.rtms-wp-container h3 {
    font-size: 1.2rem;
    font-weight: 600;
    color: #334155;
    margin-top: 1.75rem;
    margin-bottom: 0.75rem;
}
.rtms-wp-container p {
    margin-bottom: 1.25rem;
    color: #334155;
}
.rtms-wp-container ul, .rtms-wp-container ol {
    margin-bottom: 1.25rem;
    padding-left: 1.5rem;
}
.rtms-wp-container li {
    margin-bottom: 0.5rem;
    color: #334155;
}
.rtms-wp-container strong {
    color: #0f172a;
    font-weight: 600;
}
.rtms-wp-container .rtms-intro-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 5px solid #0284c7;
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin: 1.5rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}
.rtms-wp-container .rtms-diagram-box {
    background: #0f172a;
    color: #f8fafc;
    border-radius: 12px;
    padding: 24px;
    margin: 2rem 0;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
    overflow-x: auto;
}
.rtms-wp-container .rtms-diagram-svg {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
}
.rtms-wp-container table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    background: #ffffff;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border: 1px solid #e2e8f0;
}
.rtms-wp-container th {
    background: #f1f5f9;
    color: #1e293b;
    font-weight: 700;
    text-align: left;
    padding: 12px 16px;
    border-bottom: 2px solid #cbd5e1;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.rtms-wp-container td {
    padding: 12px 16px;
    border-bottom: 1px solid #e2e8f0;
    color: #334155;
    font-size: 0.95rem;
}
.rtms-wp-container tr:last-child td {
    border-bottom: none;
}
.rtms-wp-container tr:hover td {
    background: #f8fafc;
}
.rtms-wp-container .rtms-cta-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #ffffff;
    border-radius: 12px;
    padding: 2rem;
    margin: 3rem 0 1rem 0;
    text-align: center;
    box-shadow: 0 12px 30px rgba(0,0,0,0.15);
}
.rtms-wp-container .rtms-cta-banner h3 {
    color: #ffffff;
    font-size: 1.5rem;
    margin-top: 0;
    margin-bottom: 0.5rem;
}
.rtms-wp-container .rtms-cta-banner p {
    color: #94a3b8;
    max-width: 600px;
    margin: 0 auto 1.5rem auto;
}
.rtms-wp-container .rtms-cta-btn {
    display: inline-block;
    background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%);
    color: #ffffff !important;
    text-decoration: none;
    font-weight: 700;
    font-size: 1rem;
    padding: 12px 28px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.rtms-wp-container .rtms-cta-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(2, 132, 199, 0.45);
}
.rtms-wp-container .rtms-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    background: #e0f2fe;
    color: #0369a1;
}
</style>
"""

# Native standalone SVG architecture diagram to avoid any JS Mermaid dependencies on WordPress
SVG_DIAGRAM_FR = """
<div class="rtms-diagram-box">
  <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; text-align: center;">
    Topologie d'Intégration Réseau & Chiffrement RTMS
  </div>
  <svg class="rtms-diagram-svg" viewBox="0 0 920 330" xmlns="http://www.w3.org/2000/svg">
    <!-- Infrastructure Client -->
    <rect x="20" y="20" width="260" height="290" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5" />
    <text x="150" y="48" fill="#94a3b8" font-size="13" font-weight="700" text-anchor="middle">RÉSEAU CLIENT SURVEILLÉ</text>
    
    <rect x="40" y="70" width="220" height="50" rx="6" fill="#334155" stroke="#475569" />
    <text x="150" y="93" fill="#f8fafc" font-size="12" font-weight="600" text-anchor="middle">Switch Cœur / Distribution</text>
    <text x="150" y="109" fill="#94a3b8" font-size="10" text-anchor="middle">Port Mirroring (SPAN) / TAP</text>
    
    <rect x="40" y="140" width="220" height="40" rx="6" fill="#0f172a" />
    <text x="150" y="165" fill="#cbd5e1" font-size="11" text-anchor="middle">Postes de travail & Serveurs</text>

    <rect x="40" y="195" width="220" height="40" rx="6" fill="#0f172a" />
    <text x="150" y="220" fill="#cbd5e1" font-size="11" text-anchor="middle">Objets Connectés (IoT) & Imprimantes</text>

    <rect x="40" y="250" width="220" height="40" rx="6" fill="#0f172a" />
    <text x="150" y="275" fill="#cbd5e1" font-size="11" text-anchor="middle">Automates Industriels & Scada (OT)</text>

    <!-- Flèche Mirror -->
    <path d="M 260 95 L 330 95" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4,4" />
    <text x="295" y="85" fill="#38bdf8" font-size="10" font-weight="600" text-anchor="middle">Miroir</text>

    <!-- Sonde RTMS -->
    <rect x="330" y="20" width="250" height="290" rx="10" fill="#1e293b" stroke="#0284c7" stroke-width="2" />
    <text x="455" y="48" fill="#38bdf8" font-size="13" font-weight="700" text-anchor="middle">SONDE RTMS APPLIANCE</text>

    <rect x="350" y="70" width="210" height="60" rx="6" fill="#0369a1" />
    <text x="455" y="96" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">Moteur Passif (Zero-Impact)</text>
    <text x="455" y="114" fill="#bae6fd" font-size="10" text-anchor="middle">ARP, DHCP, mDNS, CDP/LLDP</text>

    <rect x="350" y="145" width="210" height="60" rx="6" fill="#4338ca" />
    <text x="455" y="171" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">Moteur d'Audit Actif Ciblé</text>
    <text x="455" y="189" fill="#c7d2fe" font-size="10" text-anchor="middle">Deep Scan, SMBv1, Open Relays</text>

    <rect x="350" y="220" width="210" height="65" rx="6" fill="#0f172a" stroke="#334155" />
    <text x="455" y="245" fill="#e2e8f0" font-size="11" font-weight="600" text-anchor="middle">Sécurité & Durcissement</text>
    <text x="455" y="261" fill="#94a3b8" font-size="9.5" text-anchor="middle">• Interface capture 100% furtive</text>
    <text x="455" y="275" fill="#94a3b8" font-size="9.5" text-anchor="middle">• Tampon local en cas de coupure</text>

    <!-- Flèche WireGuard -->
    <path d="M 580 150 L 640 150" stroke="#10b981" stroke-width="3" />
    <text x="610" y="138" fill="#10b981" font-size="10" font-weight="700" text-anchor="middle">WireGuard</text>
    <text x="610" y="170" fill="#6ee7b7" font-size="9" text-anchor="middle">Chiffré mTLS</text>

    <!-- Plateforme Centrale -->
    <rect x="640" y="20" width="260" height="290" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5" />
    <text x="770" y="48" fill="#94a3b8" font-size="13" font-weight="700" text-anchor="middle">PLATEFORME CENTRALE RTMS</text>

    <rect x="660" y="70" width="220" height="45" rx="6" fill="#0f172a" stroke="#334155" />
    <text x="770" y="93" fill="#f8fafc" font-size="11.5" font-weight="600" text-anchor="middle">Backend API & Contrôle RBAC</text>
    <text x="770" y="106" fill="#94a3b8" font-size="9.5" text-anchor="middle">Authentification mTLS & Machine ID</text>

    <rect x="660" y="125" width="220" height="45" rx="6" fill="#0f172a" stroke="#334155" />
    <text x="770" y="148" fill="#f8fafc" font-size="11.5" font-weight="600" text-anchor="middle">Microservice NVD NIST Local</text>
    <text x="770" y="161" fill="#94a3b8" font-size="9.5" text-anchor="middle">Triage CVE / CPE souverain</text>

    <rect x="660" y="180" width="220" height="45" rx="6" fill="#0f172a" stroke="#334155" />
    <text x="770" y="203" fill="#f8fafc" font-size="11.5" font-weight="600" text-anchor="middle">Base PostgreSQL Durcie</text>
    <text x="770" y="216" fill="#94a3b8" font-size="9.5" text-anchor="middle">Historique d'audit & conformité</text>

    <rect x="660" y="235" width="220" height="50" rx="6" fill="#10b981" />
    <text x="770" y="258" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">Console Web SOC & NIS2</text>
    <text x="770" y="274" fill="#d1fae5" font-size="10" text-anchor="middle">Dashboards, Alertes, Exports CMDB</text>
  </svg>
</div>
"""

SVG_DIAGRAM_EN = """
<div class="rtms-diagram-box">
  <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; text-align: center;">
    RTMS Network Integration & Encryption Topology
  </div>
  <svg class="rtms-diagram-svg" viewBox="0 0 920 330" xmlns="http://www.w3.org/2000/svg">
    <!-- Infrastructure Client -->
    <rect x="20" y="20" width="260" height="290" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5" />
    <text x="150" y="48" fill="#94a3b8" font-size="13" font-weight="700" text-anchor="middle">MONITORED CLIENT NETWORK</text>
    
    <rect x="40" y="70" width="220" height="50" rx="6" fill="#334155" stroke="#475569" />
    <text x="150" y="93" fill="#f8fafc" font-size="12" font-weight="600" text-anchor="middle">Core / Distribution Switch</text>
    <text x="150" y="109" fill="#94a3b8" font-size="10" text-anchor="middle">Port Mirroring (SPAN) / TAP</text>
    
    <rect x="40" y="140" width="220" height="40" rx="6" fill="#0f172a" />
    <text x="150" y="165" fill="#cbd5e1" font-size="11" text-anchor="middle">Workstations & Enterprise Servers</text>

    <rect x="40" y="195" width="220" height="40" rx="6" fill="#0f172a" />
    <text x="150" y="220" fill="#cbd5e1" font-size="11" text-anchor="middle">IoT Devices & Network Printers</text>

    <rect x="40" y="250" width="220" height="40" rx="6" fill="#0f172a" />
    <text x="150" y="275" fill="#cbd5e1" font-size="11" text-anchor="middle">Industrial Automata & SCADA (OT)</text>

    <!-- Mirror Arrow -->
    <path d="M 260 95 L 330 95" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4,4" />
    <text x="295" y="85" fill="#38bdf8" font-size="10" font-weight="600" text-anchor="middle">Mirror</text>

    <!-- RTMS Probe -->
    <rect x="330" y="20" width="250" height="290" rx="10" fill="#1e293b" stroke="#0284c7" stroke-width="2" />
    <text x="455" y="48" fill="#38bdf8" font-size="13" font-weight="700" text-anchor="middle">RTMS SCANNER PROBE</text>

    <rect x="350" y="70" width="210" height="60" rx="6" fill="#0369a1" />
    <text x="455" y="96" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">Passive Engine (Zero-Impact)</text>
    <text x="455" y="114" fill="#bae6fd" font-size="10" text-anchor="middle">ARP, DHCP, mDNS, CDP/LLDP</text>

    <rect x="350" y="145" width="210" height="60" rx="6" fill="#4338ca" />
    <text x="455" y="171" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">Targeted Active Audit Engine</text>
    <text x="455" y="189" fill="#c7d2fe" font-size="10" text-anchor="middle">Deep Scan, SMBv1, Open Relays</text>

    <rect x="350" y="220" width="210" height="65" rx="6" fill="#0f172a" stroke="#334155" />
    <text x="455" y="245" fill="#e2e8f0" font-size="11" font-weight="600" text-anchor="middle">Probe Hardening & Defense</text>
    <text x="455" y="261" fill="#94a3b8" font-size="9.5" text-anchor="middle">• 100% Stealth capture interface</text>
    <text x="455" y="275" fill="#94a3b8" font-size="9.5" text-anchor="middle">• Local telemetry offline buffer</text>

    <!-- WireGuard Arrow -->
    <path d="M 580 150 L 640 150" stroke="#10b981" stroke-width="3" />
    <text x="610" y="138" fill="#10b981" font-size="10" font-weight="700" text-anchor="middle">WireGuard</text>
    <text x="610" y="170" fill="#6ee7b7" font-size="9" text-anchor="middle">Encrypted mTLS</text>

    <!-- Central Platform -->
    <rect x="640" y="20" width="260" height="290" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5" />
    <text x="770" y="48" fill="#94a3b8" font-size="13" font-weight="700" text-anchor="middle">CENTRAL RTMS PLATFORM</text>

    <rect x="660" y="70" width="220" height="45" rx="6" fill="#0f172a" stroke="#334155" />
    <text x="770" y="93" fill="#f8fafc" font-size="11.5" font-weight="600" text-anchor="middle">Backend API & RBAC Controller</text>
    <text x="770" y="106" fill="#94a3b8" font-size="9.5" text-anchor="middle">mTLS Auth & Hardware Machine ID</text>

    <rect x="660" y="125" width="220" height="45" rx="6" fill="#0f172a" stroke="#334155" />
    <text x="770" y="148" fill="#f8fafc" font-size="11.5" font-weight="600" text-anchor="middle">Local NIST NVD Microservice</text>
    <text x="770" y="161" fill="#94a3b8" font-size="9.5" text-anchor="middle">Sovereign CVE / CPE Correlation</text>

    <rect x="660" y="180" width="220" height="45" rx="6" fill="#0f172a" stroke="#334155" />
    <text x="770" y="203" fill="#f8fafc" font-size="11.5" font-weight="600" text-anchor="middle">Hardened PostgreSQL Store</text>
    <text x="770" y="216" fill="#94a3b8" font-size="9.5" text-anchor="middle">Full audit logs & compliance history</text>

    <rect x="660" y="235" width="220" height="50" rx="6" fill="#10b981" />
    <text x="770" y="258" fill="#ffffff" font-size="12" font-weight="700" text-anchor="middle">Web Console & NIS2 Portal</text>
    <text x="770" y="274" fill="#d1fae5" font-size="10" text-anchor="middle">Dashboards, Alerts, CMDB Sync</text>
  </svg>
</div>
"""

CTA_FR = """
<div class="rtms-cta-banner">
  <h3>Découvrez la puissance du Scanner RTMS en action</h3>
  <p>Planifiez une démonstration personnalisée ou lancez un audit pilote dans votre environnement en moins de 15 minutes.</p>
  <a href="https://3ts.ai/contact" class="rtms-cta-btn" target="_blank" rel="noopener">Demander une Démonstration Privée &rarr;</a>
</div>
"""

CTA_EN = """
<div class="rtms-cta-banner">
  <h3>Experience the Power of the RTMS Scanner</h3>
  <p>Schedule a personalized live demo or deploy a pilot assessment in your network environment in under 15 minutes.</p>
  <a href="https://3ts.ai/contact" class="rtms-cta-btn" target="_blank" rel="noopener">Request a Live Demonstration &rarr;</a>
</div>
"""

def convert_md_to_wp_html(md_path, lang="fr"):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace mermaid block with clean standalone SVG
    svg_diagram = SVG_DIAGRAM_FR if lang == "fr" else SVG_DIAGRAM_EN
    content = re.sub(r'```mermaid[\s\S]*?```', '{{SVG_DIAGRAM}}', content)

    # Convert Markdown to HTML
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'admonition'])
    body_html = md.convert(content)

    # Restore SVG
    body_html = body_html.replace('<p>{{SVG_DIAGRAM}}</p>', svg_diagram)
    body_html = body_html.replace('{{SVG_DIAGRAM}}', svg_diagram)

    cta = CTA_FR if lang == "fr" else CTA_EN

    # Wrap in scoped container
    full_html = f"""<!-- ========================================================
     RTMS SCANNER ARCHITECTURE & CAPABILITIES
     WordPress Gutenberg Ready HTML Component
     Language: {lang.upper()}
     Generated by 3TS Consulting SRL
     ======================================================== -->
{SCOPED_CSS}
<div class="rtms-wp-container">
{body_html}
{cta}
</div>
"""
    return full_html

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # FR
    fr_md = os.path.join(DOCS_DIR, "scanner_architecture.md")
    if os.path.exists(fr_md):
        fr_html = convert_md_to_wp_html(fr_md, lang="fr")
        fr_out = os.path.join(OUTPUT_DIR, "scanner_architecture_fr.html")
        with open(fr_out, 'w', encoding='utf-8') as f:
            f.write(fr_html)
        print(f"✅ Generated: {fr_out}")

    # EN
    en_md = os.path.join(DOCS_DIR, "scanner_architecture.en.md")
    if os.path.exists(en_md):
        en_html = convert_md_to_wp_html(en_md, lang="en")
        en_out = os.path.join(OUTPUT_DIR, "scanner_architecture_en.html")
        with open(en_out, 'w', encoding='utf-8') as f:
            f.write(en_html)
        print(f"✅ Generated: {en_out}")

    # Instructions README
    readme_path = os.path.join(OUTPUT_DIR, "README_WORDPRESS.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("""# Intégration de la Documentation RTMS Scanner dans WordPress (3ts.ai)

Ce dossier contient les fichiers HTML pré-compilés, autonomes et stylisés de la page **Architecture & Capacités du Scanner RTMS**, prêts à être intégrés dans votre site WordPress `3ts.ai`.

---

## 📁 Fichiers Disponibles
1. **`scanner_architecture_fr.html`** : Version française complète avec diagramme d'architecture vectoriel (SVG) et boutons d'appel à l'action.
2. **`scanner_architecture_en.html`** : Version anglaise complète.

---

## 🚀 Comment l'intégrer dans WordPress en 30 secondes

### Méthode 1 : Éditeur Gutenberg (Recommandée)
1. Connectez-vous à votre tableau de bord WordPress (`3ts.ai/wp-admin`).
2. Allez dans **Pages** > **Ajouter une page** (ou modifiez une page existante, ex: `/rtms-scanner/` ou `/solution-rtms/`).
3. Cliquez sur le bouton **`+`** pour ajouter un bloc.
4. Recherchez et sélectionnez le bloc **HTML personnalisé** (*Custom HTML*).
5. Ouvrez le fichier `scanner_architecture_fr.html` (ou la version `.en.html`), copiez **tout le contenu** et collez-le directement dans le bloc HTML.
6. Cliquez sur **Aperçu** pour voir le résultat : la typographie, les tableaux récapitulatifs, le diagramme d'architecture et les bandeaux s'affichent automatiquement sans interférer avec votre thème WordPress !
7. Cliquez sur **Publier**.

---

### Méthode 2 : Page Builder (Elementor, Divi, WPBakery)
1. Éditez la page avec votre constructeur habituel (ex: Elementor).
2. Glissez un widget **HTML** ou **Code** dans votre section pleine largeur.
3. Collez le contenu du fichier `.html`.
4. Enregistrez la page.

---

## 🎨 Caractéristiques Techniques
- **CSS Scanné / Isolé** : Tous les styles sont préfixés par `.rtms-wp-container` pour ne pas entrer en conflit avec votre thème WordPress existant.
- **Diagramme SVG Vectoriel Inclus** : Le diagramme réseau est intégré en pur SVG. Il s'affiche instantanément, est net sur tous les écrans Retina et ne nécessite aucun plugin externe (ni script Mermaid lourd).
- **Responsive Mobile & Desktop** : S'adapte automatiquement à toutes les tailles d'écrans (smartphones, tablettes, moniteurs 4K).
- **Génération de Leads** : Un bandeau d'appel à l'action (*CTA*) élégant est inclus en bas de page pour rediriger les prospects vers votre formulaire de contact ou de démo.
""")
    print(f"✅ Generated: {readme_path}")

if __name__ == "__main__":
    main()
