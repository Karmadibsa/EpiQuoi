import React from 'react';

const LandingPage = () => {
    return (
        <div className="font-sans min-h-screen bg-white">
            {/* Header */}
            <header className="fixed w-full bg-white/90 backdrop-blur-sm z-50 border-b border-slate-100">
                <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <img src="/logo-noir.png" alt="Epitech" className="h-8 md:h-10" />
                    </div>
                    <nav className="hidden md:flex gap-8">
                        <a href="#" className="font-heading text-sm font-bold tracking-widest hover:text-epitech-blue transition-colors">PROGRAMME</a>
                        <a href="#" className="font-heading text-sm font-bold tracking-widest hover:text-epitech-blue transition-colors">CAMPUS</a>
                        <a href="#" className="font-heading text-sm font-bold tracking-widest hover:text-epitech-blue transition-colors">ENTREPRISES</a>
                        <a href="#" className="font-heading text-sm font-bold tracking-widest hover:text-epitech-blue transition-colors">ADMISSION</a>
                    </nav>
                    <div className="flex gap-4">
                        {import.meta.env.VITE_FULL_CHAT_URL && (
                            <a
                                href={import.meta.env.VITE_FULL_CHAT_URL}
                                className="hidden md:block px-4 py-2 border border-slate-900 font-heading font-bold text-sm tracking-wider hover:bg-slate-50 transition-all"
                            >
                                MODE PLEIN ÉCRAN
                            </a>
                        )}
                        <button className="bg-epitech-blue text-white px-6 py-2 font-heading font-bold text-sm tracking-wider hover:bg-epitech-dark transition-all">
                            CANDIDATER_
                        </button>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="pt-32 pb-20 px-6">
                <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-center">
                    <div className="space-y-8">
                        <h1 className="font-heading text-5xl md:text-7xl leading-tight">
                            L'ÉCOLE DE L'<br />
                            <span className="text-epitech-blue">EXCELLENCE</span><br />
                            INFORMATIQUE_
                        </h1>
                        <p className="font-body text-lg text-slate-600 max-w-lg">
                            Rejoignez Epitech et transformez votre passion pour l'informatique en une carrière d'expert. Une pédagogie par projets unique pour apprendre à apprendre.
                        </p>
                        <div className="flex gap-4">
                            <button className="px-8 py-4 bg-black text-white font-heading font-bold tracking-wider hover:bg-slate-800 transition-colors">
                                DÉCOUVRIR LE PROGRAMME
                            </button>
                            <button className="px-8 py-4 border-2 border-black font-heading font-bold tracking-wider hover:bg-black hover:text-white transition-colors">
                                JOURNÉES PORTES OUVERTES
                            </button>
                        </div>
                    </div>
                    <div className="relative">
                        <div className="absolute inset-0 bg-gradient-to-tr from-epitech-blue/20 to-transparent transform rotate-3 scale-105"></div>
                        <img
                            src="https://images.unsplash.com/photo-1571171637578-41bc2dd41cd2?ixlib=rb-4.0.3&auto=format&fit=crop&w=3540&q=80"
                            alt="Epitech Students"
                            className="relative shadow-2xl grayscale hover:grayscale-0 transition-all duration-700"
                        />
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section className="bg-black text-white py-20 px-6">
                <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-12">
                    <div className="text-center space-y-2">
                        <span className="block font-heading text-5xl md:text-6xl text-epitech-blue">100%</span>
                        <span className="font-body text-sm tracking-widest text-slate-400">D'EMPLOI EN FIN D'ÉTUDES</span>
                    </div>
                    <div className="text-center space-y-2">
                        <span className="block font-heading text-5xl md:text-6xl text-epitech-blue">20</span>
                        <span className="font-body text-sm tracking-widest text-slate-400">CAMPUS EN FRANCE & EUROPE</span>
                    </div>
                    <div className="text-center space-y-2">
                        <span className="block font-heading text-5xl md:text-6xl text-epitech-blue">5400</span>
                        <span className="font-body text-sm tracking-widest text-slate-400">ALUMNI RÉSEAU ACTIF</span>
                    </div>
                    <div className="text-center space-y-2">
                        <span className="block font-heading text-5xl md:text-6xl text-epitech-blue">3K€</span>
                        <span className="font-body text-sm tracking-widest text-slate-400">SALAIRE MOYEN DE SORTIE</span>
                    </div>
                </div>
            </section>

            {/* Info Section */}
            <section className="py-24 px-6 bg-slate-50">
                <div className="max-w-7xl mx-auto">
                    <div className="mb-16">
                        <h2 className="font-heading text-4xl mb-4">NOTRE PÉDAGOGIE_</h2>
                        <div className="w-24 h-2 bg-epitech-blue"></div>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {['PISCINE', 'PROJETS', 'STAGES'].map((item, i) => (
                            <div key={i} className="bg-white p-8 border-b-4 border-transparent hover:border-epitech-blue shadow-sm hover:shadow-xl transition-all duration-300 group">
                                <h3 className="font-heading text-2xl mb-4 group-hover:text-epitech-blue transition-colors">{item}</h3>
                                <p className="font-body text-slate-600">
                                    Une méthode d'apprentissage active où vous êtes acteur de votre formation. Apprenez en faisant, échouez pour mieux réussir.
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>
        </div>
    );
};

export default LandingPage;
