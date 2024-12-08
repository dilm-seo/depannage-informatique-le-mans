import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPhone, faEnvelope, faClock, faLocationDot, faCircleInfo } from '@fortawesome/free-solid-svg-icons';

export default function Contact() {
  return (
    <div className="py-24 gradient-bg">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-primary-light to-primary">
          Contactez-nous
        </h1>

        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
          <div className="space-y-8">
            <div className="p-6 rounded-lg card-gradient accent-border">
              <h2 className="text-2xl font-semibold mb-6">Coordonnées</h2>
              <div className="space-y-4">
                <p className="flex items-center gap-3">
                  <FontAwesomeIcon icon={faPhone} className="text-primary-light w-6" />
                  <a href="tel:0617959759" className="hover:text-primary-light transition-colors">
                    06 17 95 97 59
                  </a>
                </p>
                <p className="flex items-center gap-3">
                  <FontAwesomeIcon icon={faEnvelope} className="text-primary-light w-6" />
                  <a href="mailto:contact@reparateurpc.com" className="hover:text-primary-light transition-colors">
                    contact@reparateurpc.com
                  </a>
                </p>
                <p className="flex items-center gap-3">
                  <FontAwesomeIcon icon={faLocationDot} className="text-primary-light w-6" />
                  <span>6 impasse elisabeth vigée lebrun, Le Mans</span>
                </p>
                <p className="flex items-center gap-3">
                  <FontAwesomeIcon icon={faClock} className="text-primary-light w-6" />
                  <span>Lundi - Samedi: 9h - 19h</span>
                </p>
              </div>
            </div>

            <div className="p-6 rounded-lg card-gradient accent-border">
              <h2 className="text-2xl font-semibold mb-6">Zone d'intervention</h2>
              <p className="text-gray-300 mb-4">
                Nous intervenons principalement sur Le Mans et son agglomération. Pour les zones plus éloignées, 
                n'hésitez pas à nous contacter pour étudier la possibilité d'une intervention ou d'une assistance à distance.
              </p>
            </div>
          </div>

          <div className="space-y-8">
            <div className="p-6 rounded-lg card-gradient accent-border">
              <h2 className="text-2xl font-semibold mb-6">Comment ça marche ?</h2>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <FontAwesomeIcon icon={faCircleInfo} className="text-primary-light mt-1" />
                  <div>
                    <h3 className="font-semibold mb-1">1. Contactez-nous</h3>
                    <p className="text-gray-300">Par téléphone ou email pour décrire votre problème</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <FontAwesomeIcon icon={faCircleInfo} className="text-primary-light mt-1" />
                  <div>
                    <h3 className="font-semibold mb-1">2. Diagnostic initial</h3>
                    <p className="text-gray-300">Nous évaluons la situation et proposons une solution adaptée</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <FontAwesomeIcon icon={faCircleInfo} className="text-primary-light mt-1" />
                  <div>
                    <h3 className="font-semibold mb-1">3. Intervention</h3>
                    <p className="text-gray-300">À domicile ou à distance selon vos besoins</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <FontAwesomeIcon icon={faCircleInfo} className="text-primary-light mt-1" />
                  <div>
                    <h3 className="font-semibold mb-1">4. Suivi</h3>
                    <p className="text-gray-300">Nous restons disponibles pour tout conseil post-intervention</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}