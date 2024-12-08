import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Navigation() {
  const navItems = [
    { path: '/', label: 'Accueil' },
    { path: '/services', label: 'Services' },
    { path: '/tarifs', label: 'Tarifs' },
    { path: '/contact', label: 'Contact' }
  ];

  return (
    <nav className="bg-bg-card/50 backdrop-blur-sm sticky top-16 z-40">
      <div className="container mx-auto px-4">
        <ul className="flex justify-center space-x-8">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `py-4 px-2 inline-block text-sm font-medium transition-colors
                  ${isActive ? 'text-primary-light border-b-2 border-primary-light' : 'text-gray-300 hover:text-primary-light'}`
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}