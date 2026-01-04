import os
import requests
import time
import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlencode
from bs4 import BeautifulSoup

class LocalSnapshot:
    def __init__(self, base_dir="snapshots"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.index_file = self.base_dir / "index.json"
        self.snapshots = self.load_index()
        
    def load_index(self):
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_index(self):
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.snapshots, f, indent=2, ensure_ascii=False)
    
    def create_snapshot_id(self, url):
        """Crée un ID unique pour l'URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        parsed = urlparse(url)
        domain = parsed.netloc.replace('.', '_')
        path = parsed.path.replace('/', '_')[:20] or 'root'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{domain}_{path}_{url_hash}_{timestamp}"
    
    def _generate_captured_links_html(self, links):
        """Génère le HTML UNIQUEMENT pour les liens CAPTURÉS"""
        html_parts = []
        captured_links = []
        
        # Filtrer uniquement les liens capturés
        for link in links:
            # Vérifier si ce lien a été capturé
            for snap_id, snap_data in self.snapshots.items():
                if snap_data['url'] == link:
                    captured_links.append({
                        'url': link,
                        'snapshot_id': snap_id,
                        'title': snap_data.get('title', '')
                    })
                    break
        
        if not captured_links:
            return '<div style="color: rgba(255,255,255,0.6); font-style: italic; padding: 20px; text-align: center;">Aucun lien capturé disponible</div>'
        
        for i, link_data in enumerate(captured_links[:50]):  # Limite à 50 liens capturés
            link = link_data['url']
            snapshot_id = link_data['snapshot_id']
            truncated_link = link[:70] + "..." if len(link) > 70 else link
            
            # Déterminer l'icône selon le type de lien
            icon = "fa-link"
            if "lemonde.fr" in link:
                icon = "fa-newspaper"
            elif "youtube.com" in link or "vimeo.com" in link:
                icon = "fa-video"
            elif "github.com" in link:
                icon = "fa-code-branch"
            elif "twitter.com" in link or "facebook.com" in link:
                icon = "fa-share-alt"
            elif "reddit.com" in link:
                icon = "fa-reddit"
            elif "discord.com" in link or "discord.gg" in link:
                icon = "fa-discord"
            
            html_parts.append(f'''
            <div class="link-item captured">
                <a href="../{snapshot_id}/index.html" 
                   class="link-url" 
                   target="_blank"
                   title="{link}">
                   <i class="fab {icon}"></i>
                   {truncated_link}
                </a>
                <div class="link-status">
                    <span class="status-badge status-captured">
                        {i+1}. ✅ Disponible
                    </span>
                    <a href="../{snapshot_id}/original.html" target="_blank" style="color: #4cc9f0; font-size: 12px;">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </div>
            </div>
            ''')
        
        return ''.join(html_parts)
    
    def save_html_snapshot(self, url, html, links, title=""):
        """Sauvegarde une capture HTML et crée une version navigable"""
        snapshot_id = self.create_snapshot_id(url)
        snapshot_dir = self.base_dir / snapshot_id
        snapshot_dir.mkdir(exist_ok=True)
        
        # Fichier HTML original
        original_file = snapshot_dir / "original.html"
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Créer une version modifiée avec navigation
        self.create_navigable_html(url, html, links, snapshot_id)
        
        # Sauvegarder les métadonnées
        self.snapshots[snapshot_id] = {
            'url': url,
            'title': title[:100] if title else url,
            'timestamp': datetime.now().isoformat(),
            'snapshot_id': snapshot_id,
            'path': f"{snapshot_id}/index.html",
            'links_found': len(links),
            'links_available': list(links),
            'domain': urlparse(url).netloc
        }
        
        self.save_index()
        return snapshot_id
    
    def update_captured_links(self):
        """Met à jour la liste des liens capturés pour chaque snapshot"""
        for snap_id, snap_data in self.snapshots.items():
            captured_links = []
            
            # Vérifie quels liens de cette page ont été capturés
            for link in snap_data.get('links_available', []):
                # Cherche si ce lien a été capturé
                for other_snap in self.snapshots.values():
                    if other_snap['url'] == link:
                        captured_links.append({
                            'url': link,
                            'snapshot_id': other_snap['snapshot_id'],
                            'title': other_snap.get('title', ''),
                            'domain': urlparse(link).netloc
                        })
                        break
            
            # Met à jour les données
            snap_data['links_captured'] = captured_links
            snap_data['links_captured_count'] = len(captured_links)
        
        self.save_index()
    
    def create_navigable_html(self, url, html, links, snapshot_id):
        """Crée une version HTML avec navigation élégante et interactive"""
        # Récupérer le titre de la page
        soup_temp = BeautifulSoup(html, 'html.parser')
        page_title = soup_temp.title.string if soup_temp.title else url
        truncated_title = page_title[:60] + "..." if len(page_title) > 60 else page_title
        
        # Compter les liens capturés
        captured_count = 0
        for link in links:
            for snap_data in self.snapshots.values():
                if snap_data['url'] == link:
                    captured_count += 1
                    break
        
        # Créer l'overlay moderne
        overlay_html = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Snapshot: {truncated_title}</title>
            <style>
                :root {{
                    --primary-color: #4361ee;
                    --secondary-color: #3a0ca3;
                    --accent-color: #4cc9f0;
                    --success-color: #4ade80;
                    --warning-color: #f59e0b;
                    --danger-color: #ef4444;
                    --dark-bg: #1e293b;
                    --light-bg: #f8fafc;
                    --card-bg: #ffffff;
                    --text-dark: #1e293b;
                    --text-light: #64748b;
                    --shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                    --radius: 12px;
                    --transition: all 0.3s ease;
                }}
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .snapshot-container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: var(--card-bg);
                    border-radius: var(--radius);
                    box-shadow: var(--shadow);
                    overflow: hidden;
                    display: grid;
                    grid-template-columns: 300px 1fr;
                    min-height: 95vh;
                }}
                
                /* Sidebar Navigation */
                .sidebar {{
                    background: linear-gradient(135deg, var(--dark-bg) 0%, #2d3748 100%);
                    color: white;
                    padding: 30px 20px;
                    display: flex;
                    flex-direction: column;
                }}
                
                .logo {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }}
                
                .logo-icon {{
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(135deg, var(--accent-color), var(--primary-color));
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 20px;
                }}
                
                .logo-text {{
                    font-size: 18px;
                    font-weight: 700;
                    background: linear-gradient(135deg, var(--accent-color), white);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                
                .snapshot-info {{
                    margin-bottom: 30px;
                }}
                
                .info-card {{
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 15px;
                }}
                
                .info-label {{
                    font-size: 12px;
                    color: var(--accent-color);
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 5px;
                }}
                
                .info-value {{
                    font-size: 14px;
                    font-weight: 500;
                    word-break: break-word;
                }}
                
                .stats {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 10px;
                    margin-bottom: 30px;
                }}
                
                .stat-item {{
                    text-align: center;
                    padding: 10px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                }}
                
                .stat-number {{
                    font-size: 24px;
                    font-weight: 700;
                    color: var(--accent-color);
                }}
                
                .stat-label {{
                    font-size: 11px;
                    color: rgba(255, 255, 255, 0.6);
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                
                /* Links Panel */
                .links-panel {{
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }}
                
                .panel-title {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 15px;
                    color: white;
                    font-size: 16px;
                    font-weight: 600;
                }}
                
                .links-search {{
                    width: 100%;
                    padding: 10px 15px;
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    color: white;
                    margin-bottom: 15px;
                    font-size: 14px;
                }}
                
                .links-search::placeholder {{
                    color: rgba(255, 255, 255, 0.5);
                }}
                
                .links-list {{
                    flex: 1;
                    overflow-y: auto;
                    padding-right: 5px;
                }}
                
                .link-item {{
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 10px;
                    border-left: 3px solid var(--success-color);
                    transition: var(--transition);
                }}
                
                .link-item:hover {{
                    background: rgba(255, 255, 255, 0.1);
                    transform: translateX(5px);
                }}
                
                .link-url {{
                    display: block;
                    color: white;
                    text-decoration: none;
                    font-size: 13px;
                    line-height: 1.4;
                    margin-bottom: 5px;
                    word-break: break-all;
                }}
                
                .link-url:hover {{
                    color: var(--accent-color);
                }}
                
                .link-status {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                
                .status-badge {{
                    font-size: 11px;
                    padding: 3px 8px;
                    border-radius: 12px;
                    font-weight: 600;
                }}
                
                .status-captured {{
                    background: rgba(76, 217, 100, 0.2);
                    color: var(--success-color);
                }}
                
                /* Main Content */
                .main-content {{
                    display: flex;
                    flex-direction: column;
                }}
                
                .content-header {{
                    background: white;
                    padding: 25px 30px;
                    border-bottom: 1px solid #e2e8f0;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
                }}
                
                .breadcrumb {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    font-size: 14px;
                    color: var(--text-light);
                    margin-bottom: 15px;
                }}
                
                .breadcrumb a {{
                    color: var(--primary-color);
                    text-decoration: none;
                }}
                
                .page-title {{
                    font-size: 24px;
                    font-weight: 700;
                    color: var(--text-dark);
                    margin-bottom: 10px;
                    line-height: 1.3;
                }}
                
                .page-meta {{
                    display: flex;
                    gap: 20px;
                    font-size: 14px;
                    color: var(--text-light);
                }}
                
                .meta-item {{
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }}
                
                .action-buttons {{
                    display: flex;
                    gap: 10px;
                    margin-top: 20px;
                }}
                
                .btn {{
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 14px;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    transition: var(--transition);
                }}
                
                .btn-primary {{
                    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                    color: white;
                    border: none;
                }}
                
                .btn-primary:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(67, 97, 238, 0.3);
                }}
                
                .btn-secondary {{
                    background: var(--light-bg);
                    color: var(--text-dark);
                    border: 1px solid #e2e8f0;
                }}
                
                .btn-secondary:hover {{
                    background: #f1f5f9;
                }}
                
                /* Iframe Container */
                .iframe-container {{
                    flex: 1;
                    position: relative;
                    padding: 20px;
                }}
                
                .iframe-wrapper {{
                    width: 100%;
                    height: 100%;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: var(--shadow);
                    background: white;
                }}
                
                #page-frame {{
                    width: 100%;
                    height: 100%;
                    border: none;
                    border-radius: 10px;
                }}
                
                .loading-overlay {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    border-radius: 10px;
                    z-index: 10;
                    opacity: 0;
                    animation: fadeIn 0.5s ease forwards;
                }}
                
                .spinner {{
                    width: 50px;
                    height: 50px;
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    border-radius: 50%;
                    border-top-color: white;
                    animation: spin 1s ease-in-out infinite;
                    margin-bottom: 20px;
                }}
                
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
                
                @keyframes fadeIn {{
                    from {{ opacity: 0; }}
                    to {{ opacity: 1; }}
                }}
                
                /* Responsive */
                @media (max-width: 1024px) {{
                    .snapshot-container {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .sidebar {{
                        max-height: 400px;
                    }}
                }}
                
                /* Custom scrollbar */
                ::-webkit-scrollbar {{
                    width: 8px;
                }}
                
                ::-webkit-scrollbar-track {{
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                }}
                
                ::-webkit-scrollbar-thumb {{
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                }}
                
                ::-webkit-scrollbar-thumb:hover {{
                    background: rgba(255, 255, 255, 0.5);
                }}
                
                .no-links-message {{
                    color: rgba(255, 255, 255, 0.6);
                    font-style: italic;
                    padding: 20px;
                    text-align: center;
                    font-size: 14px;
                }}
            </style>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        </head>
        <body>
            <div class="snapshot-container">
                <!-- Sidebar Navigation -->
                <div class="sidebar">
                    <div class="logo">
                        <div class="logo-icon">
                            <i class="fas fa-archive"></i>
                        </div>
                        <div class="logo-text">Wayback Local</div>
                    </div>
                    
                    <div class="snapshot-info">
                        <div class="info-card">
                            <div class="info-label">Snapshot ID</div>
                            <div class="info-value">{snapshot_id}</div>
                        </div>
                        <div class="info-card">
                            <div class="info-label">URL</div>
                            <div class="info-value">{url[:80]}{'...' if len(url) > 80 else ''}</div>
                        </div>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-number">{len(links)}</div>
                            <div class="stat-label">Liens trouvés</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{captured_count}</div>
                            <div class="stat-label">Liens capturés</div>
                        </div>
                    </div>
                    
                    <div class="links-panel">
                        <div class="panel-title">
                            <i class="fas fa-link"></i>
                            <span>Liens disponibles ({captured_count})</span>
                        </div>
                        
                        {f'<input type="text" class="links-search" placeholder="Rechercher un lien..." onkeyup="filterLinks()">' if captured_count > 0 else ''}
                        
                        <div class="links-list" id="links-list">
                            {self._generate_captured_links_html(links)}
                        </div>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="main-content">
                    <div class="content-header">
                        <div class="breadcrumb">
                            <a href="../../index.html"><i class="fas fa-home"></i> Index</a>
                            <i class="fas fa-chevron-right"></i>
                            <span>{urlparse(url).netloc}</span>
                        </div>
                        
                        <h1 class="page-title">{truncated_title}</h1>
                        
                        <div class="page-meta">
                            <div class="meta-item">
                                <i class="fas fa-globe"></i>
                                <span>{urlparse(url).netloc}</span>
                            </div>
                            <div class="meta-item">
                                <i class="fas fa-calendar"></i>
                                <span>{datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
                            </div>
                            <div class="meta-item">
                                <i class="fas fa-database"></i>
                                <span>{len(html)//1024} KB</span>
                            </div>
                        </div>
                        
                        <div class="action-buttons">
                            <a href="original.html" target="_blank" class="btn btn-primary">
                                <i class="fas fa-file-code"></i>
                                Voir le HTML original
                            </a>
                            <a href="../../index.html" class="btn btn-secondary">
                                <i class="fas fa-list"></i>
                                Retour à l'index
                            </a>
                        </div>
                    </div>
                    
                    <div class="iframe-container">
                        <div class="iframe-wrapper">
                            <div class="loading-overlay">
                                <div class="spinner"></div>
                                <p>Chargement de la capture...</p>
                            </div>
                            <iframe id="page-frame" src="original.html"></iframe>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // Filtre des liens
                function filterLinks() {{
                    const searchTerm = document.querySelector('.links-search').value.toLowerCase();
                    const links = document.querySelectorAll('.link-item');
                    
                    let visibleCount = 0;
                    links.forEach(link => {{
                        const url = link.querySelector('.link-url').textContent.toLowerCase();
                        if (url.includes(searchTerm)) {{
                            link.style.display = 'block';
                            visibleCount++;
                        }} else {{
                            link.style.display = 'none';
                        }}
                    }});
                    
                    // Mettre à jour le titre avec le nombre de résultats
                    const panelTitle = document.querySelector('.panel-title span');
                    if (panelTitle) {{
                        panelTitle.textContent = `Liens disponibles (${{visibleCount}})`;
                    }}
                }}
                
                // Masquer le loading overlay quand l'iframe est chargée
                document.getElementById('page-frame').onload = function() {{
                    document.querySelector('.loading-overlay').style.opacity = '0';
                    setTimeout(() => {{
                        document.querySelector('.loading-overlay').style.display = 'none';
                    }}, 500);
                }};
                
                // Initialiser
                document.addEventListener('DOMContentLoaded', () => {{
                    // Ajouter un effet de hover sur les liens
                    document.querySelectorAll('.link-item').forEach(item => {{
                        item.addEventListener('click', function(e) {{
                            if (!e.target.classList.contains('link-url')) return;
                            
                            // Animation de sélection
                            document.querySelectorAll('.link-item').forEach(i => {{
                                i.style.background = '';
                            }});
                            this.style.background = 'rgba(255, 255, 255, 0.15)';
                        }});
                    }});
                }});
            </script>
        </body>
        </html>
        '''
        
        # Sauvegarder l'overlay
        overlay_file = self.base_dir / snapshot_id / "index.html"
        with open(overlay_file, 'w', encoding='utf-8') as f:
            f.write(overlay_html)
        
        return snapshot_id
    
    def generate_index_page(self):
        """Génère une page d'index pour naviguer entre toutes les captures"""
        
        # Met à jour les liens capturés avant de générer l'index
        self.update_captured_links()
        
        # Calculer les statistiques globales
        total_snapshots = len(self.snapshots)
        domains = set(s['domain'] for s in self.snapshots.values())
        total_links_found = sum(s.get('links_found', 0) for s in self.snapshots.values())
        total_links_captured = sum(s.get('links_captured_count', 0) for s in self.snapshots.values())
        coverage = round((total_links_captured / total_links_found * 100)) if total_links_found > 0 else 0
        
        html = f'''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Wayback Machine Local - Index des captures</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                header {{
                    background: linear-gradient(135deg, #2c3e50, #4a6491);
                    color: white;
                    padding: 40px;
                    text-align: center;
                }}
                h1 {{
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }}
                .stats {{
                    display: flex;
                    justify-content: center;
                    gap: 30px;
                    margin-top: 20px;
                    flex-wrap: wrap;
                }}
                .stat-box {{
                    background: rgba(255,255,255,0.1);
                    padding: 15px 25px;
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                    min-width: 180px;
                }}
                .stat-number {{
                    font-size: 2em;
                    font-weight: bold;
                    display: block;
                }}
                .stat-label {{
                    font-size: 0.9em;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 30px;
                }}
                .filters {{
                    display: flex;
                    gap: 15px;
                    margin-bottom: 30px;
                    flex-wrap: wrap;
                }}
                input, select {{
                    padding: 12px 20px;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    font-size: 16px;
                    flex: 1;
                    min-width: 200px;
                }}
                .snapshot-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
                    gap: 25px;
                    margin-top: 20px;
                }}
                .snapshot-card {{
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    transition: transform 0.3s, box-shadow 0.3s;
                    border: 1px solid #e0e0e0;
                }}
                .snapshot-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 15px 30px rgba(0,0,0,0.2);
                }}
                .card-header {{
                    background: linear-gradient(135deg, #3498db, #2980b9);
                    color: white;
                    padding: 20px;
                    position: relative;
                }}
                .card-body {{
                    padding: 20px;
                }}
                .card-footer {{
                    background: #f8f9fa;
                    padding: 15px 20px;
                    border-top: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .btn {{
                    padding: 8px 16px;
                    border-radius: 5px;
                    text-decoration: none;
                    font-weight: bold;
                    transition: all 0.3s;
                    font-size: 14px;
                }}
                .btn-view {{
                    background: #27ae60;
                    color: white;
                }}
                .btn-view:hover {{
                    background: #219653;
                }}
                .btn-original {{
                    background: #e74c3c;
                    color: white;
                }}
                .btn-original:hover {{
                    background: #c0392b;
                }}
                .btn-links {{
                    background: #9b59b6;
                    color: white;
                    margin-left: 10px;
                }}
                .btn-links:hover {{
                    background: #8e44ad;
                }}
                .timestamp {{
                    color: rgba(255,255,255,0.8);
                    font-size: 12px;
                    margin-top: 5px;
                }}
                .url {{
                    color: #2c3e50;
                    font-weight: bold;
                    margin: 10px 0;
                    word-break: break-all;
                    font-size: 14px;
                }}
                .domain-badge {{
                    display: inline-block;
                    background: #9b59b6;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    margin-right: 5px;
                }}
                .link-stats {{
                    display: flex;
                    gap: 15px;
                    margin: 10px 0;
                    font-size: 13px;
                }}
                .link-stat {{
                    display: flex;
                    align-items: center;
                    gap: 5px;
                    padding: 5px 10px;
                    background: #f1f5f9;
                    border-radius: 5px;
                }}
                .link-stat.captured {{
                    background: #d1fae5;
                    color: #065f46;
                }}
                .link-stat.available {{
                    background: #dbeafe;
                    color: #1e40af;
                }}
                .link-stat.coverage {{
                    background: #fef3c7;
                    color: #92400e;
                }}
                .link-stat i {{
                    font-size: 14px;
                }}
                .links-preview {{
                    margin-top: 10px;
                    max-height: 100px;
                    overflow-y: auto;
                    border: 1px solid #e5e7eb;
                    border-radius: 5px;
                    padding: 10px;
                    background: #f9fafb;
                    font-size: 12px;
                }}
                .link-preview-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 3px 0;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .link-preview-item:last-child {{
                    border-bottom: none;
                }}
                .link-status-dot {{
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    display: inline-block;
                    margin-right: 5px;
                }}
                .link-status-dot.captured {{
                    background: #10b981;
                }}
                @media (max-width: 768px) {{
                    .snapshot-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .filters {{
                        flex-direction: column;
                    }}
                    .stats {{
                        gap: 15px;
                    }}
                    .stat-box {{
                        min-width: 140px;
                    }}
                }}
            </style>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>🌐 Wayback Machine Local</h1>
                    <p>Naviguez dans vos captures web locales</p>
                    <div class="stats">
                        <div class="stat-box">
                            <span class="stat-number">{total_snapshots}</span>
                            <span class="stat-label">📊 Captures totales</span>
                        </div>
                        <div class="stat-box">
                            <span class="stat-number">{len(domains)}</span>
                            <span class="stat-label">🌍 Domaines</span>
                        </div>
                        <div class="stat-box">
                            <span class="stat-number">{total_links_captured}</span>
                            <span class="stat-label">🔗 Liens internes</span>
                        </div>
                        <div class="stat-box">
                            <span class="stat-number">{coverage}%</span>
                            <span class="stat-label">🎯 Couverture</span>
                        </div>
                    </div>
                </header>
                
                <div class="content">
                    <div class="filters">
                        <input type="text" id="search" placeholder="🔍 Rechercher une URL ou un titre..." onkeyup="filterSnapshots()">
                        <select id="domain-filter" onchange="filterSnapshots()">
                            <option value="">🌍 Tous les domaines</option>
                        </select>
                        <select id="sort" onchange="filterSnapshots()">
                            <option value="newest">⬇️ Plus récent</option>
                            <option value="oldest">⬆️ Plus ancien</option>
                            <option value="domain">🌍 Par domaine</option>
                            <option value="links">🔗 Plus de liens</option>
                        </select>
                    </div>
                    
                    <div id="snapshot-container" class="snapshot-grid">
                        <!-- Les cartes seront générées ici par JavaScript -->
                    </div>
                </div>
            </div>
            
            <script>
                const snapshots = {json.dumps(list(self.snapshots.values()), ensure_ascii=False)};
                
                function filterSnapshots() {{
                    const search = document.getElementById('search').value.toLowerCase();
                    const domain = document.getElementById('domain-filter').value;
                    const sort = document.getElementById('sort').value;
                    
                    let filtered = snapshots.filter(s => {{
                        const matchesSearch = s.url.toLowerCase().includes(search) || 
                                              (s.title && s.title.toLowerCase().includes(search)) ||
                                              s.snapshot_id.toLowerCase().includes(search);
                        const matchesDomain = !domain || s.domain === domain;
                        return matchesSearch && matchesDomain;
                    }});
                    
                    // Trier
                    if (sort === 'newest') {{
                        filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                    }} else if (sort === 'oldest') {{
                        filtered.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                    }} else if (sort === 'domain') {{
                        filtered.sort((a, b) => a.domain.localeCompare(b.domain));
                    }} else if (sort === 'links') {{
                        filtered.sort((a, b) => (b.links_captured_count || 0) - (a.links_captured_count || 0));
                    }}
                    
                    renderSnapshots(filtered);
                }}
                
                function renderSnapshots(snapshots) {{
                    const container = document.getElementById('snapshot-container');
                    container.innerHTML = '';
                    
                    snapshots.forEach(snap => {{
                        const date = new Date(snap.timestamp);
                        const capturedCount = snap.links_captured_count || 0;
                        const totalLinks = snap.links_found || 0;
                        const coverage = totalLinks > 0 ? Math.round((capturedCount / totalLinks) * 100) : 0;
                        
                        // Préparer la preview des liens
                        let linksPreview = '';
                        if (snap.links_captured && snap.links_captured.length > 0) {{
                            linksPreview = '<div class="links-preview">';
                            snap.links_captured.slice(0, 3).forEach(link => {{
                                const truncated = link.url.length > 50 ? link.url.substring(0, 50) + '...' : link.url;
                                linksPreview += `
                                    <div class="link-preview-item">
                                        <span><span class="link-status-dot captured"></span>${{truncated}}</span>
                                        <a href="${{link.snapshot_id}}/index.html" target="_blank" style="color: #3b82f6; font-size: 10px;">
                                            <i class="fas fa-external-link-alt"></i>
                                        </a>
                                    </div>
                                `;
                            }});
                            if (snap.links_captured.length > 3) {{
                                linksPreview += `<div style="text-align: center; color: #6b7280; font-size: 11px; padding: 5px;">
                                    + ${{snap.links_captured.length - 3}} autres liens...
                                </div>`;
                            }}
                            linksPreview += '</div>';
                        }}
                        
                        const card = `
                            <div class="snapshot-card">
                                <div class="card-header">
                                    <span class="domain-badge">${{snap.domain}}</span>
                                    <div class="timestamp">${{date.toLocaleString('fr-FR')}}</div>
                                </div>
                                <div class="card-body">
                                    <div class="url" title="${{snap.url}}">
                                        ${{snap.url.length > 60 ? snap.url.substring(0, 60) + '...' : snap.url}}
                                    </div>
                                    
                                    <div class="link-stats">
                                        <div class="link-stat captured">
                                            <i class="fas fa-link"></i>
                                            <span>${{capturedCount}} capturés</span>
                                        </div>
                                        <div class="link-stat available">
                                            <i class="fas fa-external-link-alt"></i>
                                            <span>${{totalLinks}} trouvés</span>
                                        </div>
                                        ${{coverage > 0 ? `
                                        <div class="link-stat coverage">
                                            <i class="fas fa-chart-line"></i>
                                            <span>${{coverage}}% couverture</span>
                                        </div>` : ''}}
                                    </div>
                                    
                                    ${{linksPreview}}
                                    
                                    <div style="font-size: 12px; color: #7f8c8d; margin-top: 10px;">
                                        ID: ${{snap.snapshot_id}}
                                    </div>
                                </div>
                                <div class="card-footer">
                                    <div>
                                        <a href="${{snap.path}}" class="btn btn-view" target="_blank">
                                            <i class="fas fa-eye"></i> Voir
                                        </a>
                                        <a href="${{snap.path.replace('index.html', 'original.html')}}" 
                                           class="btn btn-original" target="_blank">
                                            <i class="fas fa-code"></i> Original
                                        </a>
                                        ${{capturedCount > 0 ? `
                                        <a href="${{snap.path}}" class="btn btn-links" target="_blank">
                                            <i class="fas fa-sitemap"></i> Liens (${{capturedCount}})
                                        </a>` : ''}}
                                    </div>
                                </div>
                            </div>
                        `;
                        container.innerHTML += card;
                    }});
                    
                    // Mettre à jour les options de filtre de domaine
                    const domainSelect = document.getElementById('domain-filter');
                    const domains = [...new Set(snapshots.map(s => s.domain))];
                    
                    // Réinitialiser les options (garder la première)
                    while (domainSelect.options.length > 1) {{
                        domainSelect.remove(1);
                    }}
                    
                    domains.sort().forEach(domain => {{
                        const option = document.createElement('option');
                        option.value = domain;
                        option.textContent = domain;
                        domainSelect.appendChild(option);
                    }});
                }}
                
                // Initialisation
                document.addEventListener('DOMContentLoaded', () => {{
                    filterSnapshots();
                }});
            </script>
        </body>
        </html>
        '''
        
        index_file = self.base_dir / "index.html"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Index généré: {index_file}")
        return str(index_file)

class WebScraperWithSnapshots:
    def __init__(self, base_dir="snapshots", delay=1, max_depth=3, max_pages=100):
        self.snapshot = LocalSnapshot(base_dir)
        self.visited = set()
        self.delay = delay
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.pages_scraped = 0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def fetch_html(self, url):
        """Récupère le contenu HTML d'une URL"""
        try:
            time.sleep(self.delay)
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except Exception as e:
            print(f"❌ Erreur lors du fetch {url}: {e}")
            return None
    
    def extract_links(self, html, base_url):
        """Extrait tous les liens d'une page HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        for tag in soup.find_all(['a', 'link'], href=True):
            href = tag['href']
            abs_url = urljoin(base_url, href)
            if urlparse(abs_url).scheme in ['http', 'https']:
                links.add(abs_url)
        
        return links
    
    def scrape_page(self, url, depth):
        """Scrape une page unique et crée une capture"""
        if (depth > self.max_depth or 
            url in self.visited or 
            self.pages_scraped >= self.max_pages):
            return set()
        
        print(f"📥 Scraping (niveau {depth}): {url}")
        
        html = self.fetch_html(url)
        if not html:
            return set()
        
        self.visited.add(url)
        self.pages_scraped += 1
        
        # Extraire les liens
        links = self.extract_links(html, url)
        print(f"   🔗 Trouvé {len(links)} liens")
        
        # Extraire le titre de la page
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else url
        
        # Créer la capture
        snapshot_id = self.snapshot.save_html_snapshot(url, html, links, title)
        print(f"   💾 Capture créée: {snapshot_id}")
        
        return links
    
    def crawl(self, start_url):
        """Lance le crawling récursif"""
        print(f"🚀 Démarrage du crawling depuis: {start_url}")
        print(f"⚙️  Configuration: profondeur={self.max_depth}, délai={self.delay}s, max={self.max_pages} pages")
        print("=" * 60)
        
        to_visit = [(start_url, 0)]
        
        while to_visit and self.pages_scraped < self.max_pages:
            url, depth = to_visit.pop(0)
            
            if url not in self.visited and depth <= self.max_depth:
                new_links = self.scrape_page(url, depth)
                
                # Ajouter les nouveaux liens à visiter
                for link in new_links:
                    if link not in self.visited:
                        to_visit.append((link, depth + 1))
        
        # Générer l'index final
        index_path = self.snapshot.generate_index_page()
        print("=" * 60)
        print(f"✅ Crawling terminé!")
        print(f"📊 Statistiques:")
        print(f"   Pages visitées: {len(self.visited)}")
        print(f"   Captures créées: {len(self.snapshot.snapshots)}")
        print(f"   Liens internes capturés: {sum(s.get('links_captured_count', 0) for s in self.snapshot.snapshots.values())}")
        print(f"   Dossier des captures: {self.snapshot.base_dir}")
        print(f"   📍 Index principal: file://{os.path.abspath(index_path)}")
        print("\n💡 Ouvrez le fichier index.html dans votre navigateur pour naviguer!")

def main():
    print("""
    🌐 WEB SCRAPER AVEC CAPTURES LOCALES
    ====================================
    Ce programme va:
    1. Scraper les pages web
    2. Créer des captures HTML locales
    3. Générer une interface de navigation
    4. Montrer UNIQUEMENT les liens capturés
    """)
    
    # Configuration
    start_url = input("Entrez l'URL de départ: ").strip()
    
    try:
        max_depth = int(input("Profondeur de crawling (1-4 recommandé): ").strip())
        max_pages = int(input("Nombre maximum de pages à scraper (10-100): ").strip())
        delay = float(input("Délai entre les requêtes (secondes, 1-3 recommandé): ").strip())
    except ValueError:
        print("⚠️  Utilisation des valeurs par défaut")
        max_depth = 2
        max_pages = 20
        delay = 1
    
    # Créer et lancer le scraper
    scraper = WebScraperWithSnapshots(
        base_dir="wayback_snapshots",
        delay=delay,
        max_depth=max_depth,
        max_pages=max_pages
    )
    
    scraper.crawl(start_url)
    
    print("\n🎯 Comment utiliser les captures:")
    print("1. Ouvrez 'wayback_snapshots/index.html' dans votre navigateur")
    print("2. Naviguez entre les captures via l'interface web")
    print("3. Chaque capture montre UNIQUEMENT les liens déjà capturés")
    print("4. Plus de liens non-capturés visibles - seulement les disponibles!")

if __name__ == "__main__":
    main()