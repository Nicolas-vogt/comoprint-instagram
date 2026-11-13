# Carrousel Instagram Comoprint : guide d'installation

Affiche les 6 dernières publications Instagram de Comoprint sur la page d'accueil de comoprint.com. Coût : 0 €. Maintenance : aucune après installation. Aucun compte développeur Meta ou Facebook n'est nécessaire.

## Fonctionnement

1. Behold (offre gratuite) se connecte au compte Instagram Comoprint et met à disposition un flux des dernières publications.
2. Chaque nuit, GitHub Actions lit ce flux une seule fois, télécharge les 6 images (carrées, 640 px, format WebP) et écrit `docs/feed.json`.
3. GitHub Pages publie ce dossier `docs` sur une adresse publique.
4. Le bloc HTML collé dans le back office lit `feed.json` et affiche le carrousel.

Une lecture par jour représente environ 30 vues par mois, pour une limite gratuite de 1 200 chez Behold. Les visiteurs de comoprint.com ne contactent jamais Behold.

Si une exécution échoue, le carrousel continue d'afficher les publications de la veille et GitHub envoie un email d'alerte. Si le flux est inaccessible, le bloc reste masqué : aucun cadre vide sur la page.

Durée d'installation estimée : 30 minutes.

## Étape 1 : compte Instagram professionnel

Dans l'application Instagram du compte Comoprint : Paramètres > Type de compte et outils. Le compte doit être « Professionnel » (Entreprise ou Créateur). Passer à l'étape 2 s'il l'est déjà.

## Étape 2 : flux Behold

1. Créer un compte gratuit sur behold.so (offre Free).
2. « Add source » : connecter le compte Instagram Comoprint avec ses identifiants Instagram.
3. « Add feed » > type **JSON** (et non « Widget »), nombre de publications : 6.
4. Copier l'adresse du flux, de la forme `https://feeds.behold.so/XXXXXXXX`.
5. Ne pas activer la restriction par domaine (« domain whitelist ») : la requête vient de GitHub, pas de comoprint.com.

## Étape 3 : dépôt GitHub

1. Sur github.com : « New repository ». Nom : `comoprint-instagram`. Visibilité : **Public** (obligatoire pour GitHub Pages gratuit ; seuls les images et le fichier JSON sont publics, l'adresse du flux Behold reste dans les secrets).
2. Déposer les fichiers du dossier en respectant l'arborescence :
   ```
   .github/workflows/instagram.yml
   scripts/fetch_behold.py
   scripts/fetch_instagram.py
   .gitignore
   README.md
   ```
   Le plus simple : « Add file » > « Upload files », glisser le contenu du dossier dézippé. Le dossier `.github` étant masqué sur Mac et Windows, vérifier qu'il apparaît bien dans le dépôt après envoi. S'il manque : « Add file » > « Create new file », taper `.github/workflows/instagram.yml` comme nom, coller le contenu.

   Les deux scripts sont nécessaires : `fetch_behold.py` utilise des fonctions de `fetch_instagram.py`.

## Étape 4 : secret

Dans le dépôt : Settings > Secrets and variables > Actions > « New repository secret ».

| Nom | Valeur |
|---|---|
| `BEHOLD_FEED_URL` | L'adresse du flux Behold copiée à l'étape 2 |

C'est le seul secret nécessaire : Behold gère lui-même le renouvellement de l'autorisation Instagram.

## Étape 5 : activer GitHub Pages et lancer une première fois

1. Onglet **Actions** : accepter l'activation des workflows si GitHub le demande. Cliquer sur « Flux Instagram Comoprint » > « Run workflow ». Attendre la coche verte (environ 1 minute). Un dossier `docs` apparaît dans le dépôt.
2. Settings > Pages > Source : « Deploy from a branch ». Branche `main`, dossier `/docs`. Enregistrer.
3. Après 1 à 2 minutes, ouvrir `https://VOTRE-COMPTE.github.io/comoprint-instagram/feed.json` (remplacer `VOTRE-COMPTE` par l'identifiant GitHub). Le fichier doit lister 6 publications.

## Étape 6 : alertes en cas d'échec

Photo de profil > Settings > Notifications > section « Actions » : cocher « Email » et « Only notify for failed workflows ». Aucune intervention n'est attendue au quotidien ; un email signale seulement un problème.

## Étape 7 : intégration sur la page d'accueil

1. Ouvrir `bloc-homepage.html`, remplacer `VOTRE-COMPTE` dans la ligne `FEED_URL` par l'identifiant GitHub.
2. Coller l'intégralité du bloc dans le bloc HTML personnalisé de la page d'accueil, dans le back office.
3. Revalider la page : onglet « Visibilité » > « Enregistrer ».
4. Contrôler sur comoprint.com en navigation privée, sur ordinateur et sur mobile.

Si le bloc n'apparaît pas : clic droit > Inspecter > rechercher `cp-ig`. Si la balise `<script>` a disparu, le back office filtre le JavaScript : il faut alors demander à Unik d'autoriser ce script sur la page d'accueil.

## Maintenance

Aucune action récurrente. Le script tourne chaque nuit et met le flux à jour.

Interventions possibles :
- **Mot de passe Instagram modifié** : Behold peut perdre la connexion. Reconnecter le compte dans le tableau de bord Behold ; l'adresse du flux ne change pas.
- **Email d'échec GitHub** : ouvrir l'onglet Actions du dépôt pour lire le message d'erreur.

Le commit quotidien du script maintient le dépôt actif : GitHub ne suspend donc pas la tâche planifiée, ce qu'il fait sur un dépôt public sans activité depuis 60 jours.

## Mesure

Chaque clic dans le bloc envoie l'événement GA4 `instagram_click` (paramètre `link_text` : `post` ou `follow`), si la balise GA4 est chargée via gtag sur la page. Avec Google Tag Manager à la place de gtag, l'événement n'est pas envoyé : le signaler pour adapter le code.
