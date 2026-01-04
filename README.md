# Informatique-L2# 🌐 Web Scraper - Wayback Local

## 🚀 Installation rapide


```bash
# 1. Installer Python 3.11+
# 2. Télécharger le projet
git clone https://github.com/votre-repo/web-scraper.git
cd web-scraper

# 3. Installer les dépendances
pip install requests beautifulsoup4

# 4. Lancer le programme
python scraper.py
```

## 📋 Utilisation

1. **Lancez le programme** :
   ```bash
   python scraper.py
   ```

2. **Répondez aux questions** :
   ```
   🌐 WEB SCRAPER AVEC CAPTURES LOCALES
   ====================================
   
   Entrez l'URL de départ: https://example.com
   Profondeur de crawling (1-4 recommandé): 2
   Nombre maximum de pages à scraper (10-100): 20
   Délai entre les requêtes (secondes, 1-3 recommandé): 1.5
   ```

3. **Attendez la fin du scraping** :
   - Le programme va automatiquement visiter les pages
   - Créer des captures locales
   - Générer une interface de navigation

4. **Naviguez dans vos captures** :
   - Ouvrez `wayback_snapshots/index.html` dans votre navigateur
   - Explorez les captures via l'interface web moderne
   - Utilisez la recherche et les filtres

## ⚙️ Recommandations

- **Démarrage** : Commencez avec profondeur=2, max_pages=20
- **Délai** : Utilisez 1-3 secondes pour respecter les sites
- **Tests** : Essayez d'abord sur des sites simples
- **Éthique** : Ne scrapez pas massivement sans autorisation

## 📁 Structure générée

```
wayback_snapshots/
├── index.html              # Interface principale
├── index.json              # Base de données
├── example_com_xxx/        # Capture 1
│   ├── index.html         # Version navigable
│   └── original.html      # Version originale
└── ... autres captures
```

## 🛠 Dépendances

- Python 3.11+
- `requests` (téléchargement web)
- `beautifulsoup4` (analyse HTML)

## ❓ Aide

Pour toute question :
1. Vérifiez que Python 3.11+ est installé
2. Installez les dépendances avec `pip install`
3. Lisez les messages d'erreur dans la console
4. Testez avec une URL simple (ex: `https://example.com`)

---

**💡 Conseil** : Ouvrez toujours `wayback_snapshots/index.html` pour naviguer dans vos archives !
```
