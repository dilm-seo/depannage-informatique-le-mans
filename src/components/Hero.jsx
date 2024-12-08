import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faLaptopMedical, faHome, faVideo } from '@fortawesome/free-solid-svg-icons';

export default function Hero() {
  return (
    <section className="min-h-screen pt-24 pb-12 gradient-bg">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-6xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-primary-light to-primary">
            Expert en Dépannage Informatique
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Intervention à domicile sur Le Mans et assistance à distance
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {[
            {
              icon: faLaptopMedical,
              title: "Dépannage PC",
              description: "Résolution rapide de vos problèmes informatiques par un expert qualifié"
            },
            {
              icon: faHome,
              title: "À Domicile",
              description: "Intervention directement chez vous pour plus de confort et d'efficacité"
            },
            {
              icon: faVideo,
              title: "Assistance Distance",
              description: "Support technique à distance pour une résolution rapide de vos problèmes"
            }
          ].map((service, index) => (
            <div key={index} className="p-6 rounded-lg hover-card card-gradient accent-border">
              <FontAwesomeIcon icon={service.icon} className="text-4xl mb-4 text-primary-light" />
              <h3 className="text-xl font-semibold mb-3">{service.title}</h3>
              <p className="text-gray-400">{service.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}