import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck, faClock, faHome, faVideo } from '@fortawesome/free-solid-svg-icons';

export default function Pricing() {
  const features = [
    "Diagnostic complet de votre système",
    "Déplacement inclus sur Le Mans",
    "Assistance téléphonique prioritaire",
    "Conseils personnalisés",
    "Suivi après intervention",
    "Garantie satisfaction"
  ];

  return (
    <div className="py-24 gradient-bg">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-primary-light to-primary">
          Nos Tarifs
        </h1>
        
        <div className="max-w-4xl mx-auto">
          <div className="p-8 rounded-lg card-gradient accent-border">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">Tarification Simple et Transparente</h2>
              <div className="text-5xl font-bold text-primary-light mb-4">
                30€ <span className="text-xl text-gray-400">/heure</span>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div>
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <FontAwesomeIcon icon={faClock} className="text-primary-light" />
                  Durée Moyenne des Interventions
                </h3>
                <ul className="space-y-2 text-gray-300">
                  <li>• Virus/Malware : 1-2 heures</li>
                  <li>• Optimisation PC : 1-2 heures</li>
                  <li>• Installation Windows : 2-3 heures</li>
                  <li>• Problème réseau : 1 heure</li>
                </ul>
              </div>

              <div>
                <h3 className="text-xl font-semibold mb-4">Services Inclus</h3>
                <ul className="space-y-2">
                  {features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2 text-gray-300">
                      <FontAwesomeIcon icon={faCheck} className="text-primary-light" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-8">
              <div className="p-6 rounded-lg bg-bg-dark/50">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <FontAwesomeIcon icon={faHome} className="text-primary-light" />
                  Intervention à Domicile
                </h3>
                <p className="text-gray-300">
                  Déplacement gratuit sur Le Mans. Intervention sur place pour un service personnalisé et efficace.
                </p>
              </div>

              <div className="p-6 rounded-lg bg-bg-dark/50">
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <FontAwesomeIcon icon={faVideo} className="text-primary-light" />
                  Assistance à Distance
                </h3>
                <p className="text-gray-300">
                  Solution rapide et économique pour les problèmes simples. Sécurisé et professionnel.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}