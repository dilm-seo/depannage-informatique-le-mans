import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faVirus, faMemory, faNetworkWired, faShieldVirus, faSpinner, faDesktop } from '@fortawesome/free-solid-svg-icons';

export default function Services() {
  const services = [
    {
      icon: faVirus,
      title: "Suppression Virus",
      description: "Nettoyage complet de votre ordinateur des virus et logiciels malveillants"
    },
    {
      icon: faMemory,
      title: "Optimisation PC",
      description: "Amélioration des performances de votre ordinateur"
    },
    {
      icon: faNetworkWired,
      title: "Problèmes Réseau",
      description: "Résolution des problèmes de connexion Internet et configuration réseau"
    },
    {
      icon: faShieldVirus,
      title: "Sécurisation",
      description: "Installation et configuration d'antivirus et pare-feu"
    },
    {
      icon: faSpinner,
      title: "PC Lent",
      description: "Diagnostic et résolution des problèmes de lenteur"
    },
    {
      icon: faDesktop,
      title: "Installation Windows",
      description: "Installation et configuration de votre système d'exploitation"
    }
  ];

  return (
    <section className="py-16 gradient-bg" id="services">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-primary-light to-primary">
          Nos Services
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {services.map((service, index) => (
            <div key={index} className="p-6 rounded-lg hover-card card-gradient accent-border">
              <FontAwesomeIcon icon={service.icon} className="text-3xl mb-4 text-primary-light" />
              <h3 className="text-xl font-semibold mb-3">{service.title}</h3>
              <p className="text-gray-400">{service.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}