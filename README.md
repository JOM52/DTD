# ⚡ DTD – Détecteur de Tension Distant

## 🧭 Aperçu du projet

Le **projet DTD** (Détecteur de Tension Distant) a pour objectif de créer un système permettant à un contrôleur électricien de vérifier la correspondance entre les disjoncteurs du tableau électrique et les circuits réels dans un bâtiment.

Il se compose de deux éléments principaux :

- **TA** : Terminal Afficheur (basé sur LilyGO T-Display-S3 + module radio GT38)  
- **DD** : Détecteur Distant (basé sur ESP32-WROOM-32 + module radio GT38)

Le **TA** communique avec plusieurs **DD** (jusqu’à 5 simultanément) via une liaison radio 433 MHz.  
Chaque DD détecte la présence de tension sur un circuit et renvoie cette information au terminal.

---

## ⚙️ Architecture du système

### 🔹 Composants matériels

| Élément | Description | Microcontrôleur | Radio | Alimentation |
|----------|--------------|----------------|--------|---------------|
| **TA** | Terminal de test avec affichage       | LilyGO T-Display-S3 (ESP32-S3) | GT38 (SI4438/4463) | USB-C / batterie |
| **DD** | Détecteur de tension distant | ESP32-WROOM-32 | GT38 (SI4438/4463) | 230 V via optocoupleur H11AA1 |
