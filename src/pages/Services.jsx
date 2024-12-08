import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faVirus, faMemory, faNetworkWired, faShieldVirus, 
  faSpinner, faDesktop, faDatabase, faWrench, 
  faLaptop, faCloud, faTools, faServer 
} from '@fortawesome/free-solid-svg-icons';

export default function Services() {
  const services = [
    {
      icon: faVirus,
      title: "Suppression de Virus",
      description: "Détection et élimination complète des virus, malwares, et logiciels espions. Protection de vos données personnelles et restauration de la sécurité de votre système."
    },
    {
      icon: faMemory,
      title: "Optimisation PC",
      description: "Analyse approfondie et optimisation des performances. Nettoyage du système, mise à jour des pilotes, et configuration optimale pour une utilisation fluide."
    },
    {
      icon: faNetworkWired,
      title: "Configuration Réseau",
      description: "Installation et configuration de votre réseau WiFi, partage de fichiers, imprimantes réseau. Sécurisation de votre connexion et optimisation du débit."
    },
    {
      icon: faShieldVirus,
      title: "Sécurisation",
      description: "Mise en place d'une protection complète : antivirus, pare-feu, contrôle parental. Formation aux bonnes pratiques de sécurité informatique."
    },
    {
      icon: faSpinner,
      title: "Résolution Lenteurs",
      description: "Diagnostic approfondi des causes de ralentissement. Optimisation du démarrage, nettoyage des fichiers temporaires, défragmentation si nécessaire."
    },
    {
      icon: faDesktop,
      title: "Installation Windows",
      description: "Installation propre de Windows, configuration initiale, installation des pilotes et logiciels essentiels. Sauvegarde préalable de vos données."
    },
    {
      icon: faDatabase,
      title: "Sauvegarde Données",
      description: "Mise en place de solutions de sauvegarde automatique. Récupération de données perdues ou supprimées accidentellement."
    },
    {
      icon: faWrench,
      title: "Maintenance Préventive",
      description: "Vérification régulière de l'état de votre système, mises à jour de sécurité, nettoyage physique des composants."
    },
    {
      icon: faLaptop,
      title: "Réparation Matérielle",
      description: "Diagnostic et réparation des problèmes matériels : écran, clavier, batterie, disque dur. Remplacement de composants défectueux."
    },
    {
      icon: faCloud,
      title: "Solutions Cloud",
      description: "Configuration des services cloud (Google Drive, OneDrive), synchronisation des données, sauvegardes en ligne."
    },
    {
      icon: faTools,
      title: "Formation Utilisateur",
      description: "Formation personnalisée à l'utilisation de votre ordinateur, des logiciels courants, et aux bonnes pratiques de sécurité."
    },
    {
      icon: faServer,
      title: "Assistance à Distance",
      description: "Support technique à distance pour une résolution rapide des problèmes simples. Intervention sécurisée via des outils professionnels."
    }
  ];

  return (
    <div className="py-24 gradient-bg">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-primary-light to-primary">
          Nos Services Détaillés
        </h1>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {services.map((service, index) => (
            <div key={index} className="p-6 rounded-lg hover-card card-gradient accent-border">
              <FontAwesomeIcon icon={service.icon} className="text-3xl mb-4 text-primary-light" />
              <h3 className="text-xl font-semibold mb-3">{service.title}</h3>
              <p className="text-gray-400">{service.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}