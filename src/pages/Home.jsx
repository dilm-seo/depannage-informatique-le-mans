import React from 'react';
import Hero from '../components/Hero';
import ServicesSummary from '../components/ServicesSummary';

export default function Home() {
  return (
    <div className="gradient-bg">
      <Hero />
      <ServicesSummary />
    </div>
  );
}