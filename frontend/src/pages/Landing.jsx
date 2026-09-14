import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Anchor, Waves, Database } from 'lucide-react';
import watercolorImg from '../assets/ocean_watercolor.jpg';

const Landing = ({ onLaunch }) => {
  const containerRef = useRef(null);
  
  // Track scroll inside the deep dive container
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  // Timings for Layer 1 (Left) - Make it visible immediately!
  const l1Opacity = useTransform(scrollYProgress, [0, 0.2, 0.3], [1, 1, 0]);
  const l1Y = useTransform(scrollYProgress, [0, 0.2, 0.3], [0, 0, -60]);
  const l1Scale = useTransform(scrollYProgress, [0, 0.2], [1, 1]);

  // Timings for Layer 2 (Right)
  const l2Opacity = useTransform(scrollYProgress, [0.2, 0.35, 0.55, 0.65], [0, 1, 1, 0]);
  const l2Y = useTransform(scrollYProgress, [0.2, 0.35, 0.55, 0.65], [60, 0, 0, -60]);
  const l2Scale = useTransform(scrollYProgress, [0.2, 0.35], [0.9, 1]);

  // Timings for Layer 3 (Center)
  const l3Opacity = useTransform(scrollYProgress, [0.55, 0.7, 1], [0, 1, 1]);
  const l3Y = useTransform(scrollYProgress, [0.55, 0.7], [60, 0]);
  const l3Scale = useTransform(scrollYProgress, [0.55, 0.7], [0.9, 1]);

  return (
    <div 
      className="w-full font-sans relative text-[var(--color-aubergine-ink)]"
      style={{
        background: 'linear-gradient(180deg, var(--color-linen) 0%, var(--color-linen) 90vh, #cae9ff 130vh, #62b6cb 200vh, #1b4965 300vh, #0a192f 100%)'
      }}
    >
      
      {/* 1. TOP NAVIGATION */}
      <nav className="absolute top-0 left-0 w-full h-[72px] flex justify-between items-center px-6 md:px-[60px] z-50">
        <div className="flex items-center gap-2 text-[var(--color-aubergine-ink)] font-medium text-[16px]">
          <span className="text-[20px]">✱</span> OCEANEMBED
        </div>
        
        <div className="hidden md:flex items-center gap-8 text-[14px] font-normal text-[var(--color-aubergine-ink)]">
          <button className="hover:opacity-70 transition-opacity">Dataset</button>
          <button className="hover:opacity-70 transition-opacity">Architecture</button>
          <button className="hover:opacity-70 transition-opacity">Predictions</button>
        </div>

        <button 
          onClick={onLaunch}
          className="bg-[var(--color-espresso)] text-white text-[14px] px-[18px] py-[10px] rounded-[999px] font-normal hover:opacity-90 transition-opacity"
        >
          Launch Console
        </button>
      </nav>

      {/* 2. WATERCOLOR HERO SECTION */}
      <section className="relative w-full min-h-[90vh] flex flex-col items-center justify-start pt-[30vh]">
        <div className="absolute top-0 left-0 w-full h-[70vh] z-0 overflow-hidden">
          <img 
            src={watercolorImg} 
            alt="Ocean Watercolor Sunset" 
            className="w-full h-full object-cover object-center"
          />
          <div className="absolute bottom-0 left-0 w-full h-[250px] bg-gradient-to-t from-[var(--color-linen)] via-[var(--color-linen)]/80 to-transparent"></div>
        </div>

        <div className="relative z-10 flex flex-col items-center text-center w-full max-w-[1000px] mx-auto mt-[10vh] px-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="bg-[var(--color-espresso)]/80 backdrop-blur-md text-white text-[13px] px-[16px] py-[8px] rounded-[999px] mb-8 flex items-center justify-center gap-2 cursor-pointer hover:bg-[var(--color-charcoal)] transition-colors"
          >
            OceanEmbed reaches 1000m depth <span className="text-[10px]">❯</span>
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
            className="text-[48px] md:text-[80px] font-normal leading-[1.05] tracking-[-0.04em] text-[var(--color-aubergine-ink)] mb-8 text-center mx-auto max-w-[900px]"
          >
            Defining the future of subsurface prediction
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
            className="text-[18px] md:text-[22px] font-light leading-[1.6] text-[var(--color-stone)] max-w-[760px] mx-auto mb-12 text-center"
          >
            Meet the AI-native telemetry infrastructure that accelerates deep ocean reanalysis, automates layer mapping, and reduces computational costs.
          </motion.p>

          <motion.button 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
            onClick={onLaunch}
            className="bg-[var(--color-espresso)] text-white text-[16px] px-[36px] py-[18px] rounded-[60px] font-normal hover:bg-[var(--color-charcoal)] transition-colors"
          >
            Get started
          </motion.button>
        </div>
      </section>

      {/* 3. STAT BLOCK */}
      <section className="w-full max-w-[1200px] mx-auto px-6 md:px-[60px] pt-[80px] pb-[20px] grid grid-cols-1 md:grid-cols-3 gap-16 text-center relative z-10">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-10%" }} transition={{ duration: 0.8 }}>
          <div className="text-[72px] md:text-[88px] font-normal tracking-[-0.05em] leading-[1.0] text-[var(--color-aubergine-ink)] mb-3">15</div>
          <div className="text-[15px] font-light text-[var(--color-stone)] mix-blend-color-burn">Standard depth layers mapped</div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-10%" }} transition={{ duration: 0.8, delay: 0.1 }}>
          <div className="text-[72px] md:text-[88px] font-normal tracking-[-0.05em] leading-[1.0] text-[var(--color-aubergine-ink)] mb-3">1000m</div>
          <div className="text-[15px] font-light text-[var(--color-stone)] mix-blend-color-burn">Maximum prediction depth</div>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-10%" }} transition={{ duration: 0.8, delay: 0.2 }}>
          <div className="text-[72px] md:text-[88px] font-normal tracking-[-0.05em] leading-[1.0] text-[var(--color-aubergine-ink)] mb-3">0.25°</div>
          <div className="text-[15px] font-light text-[var(--color-stone)] mix-blend-color-burn">Spatial resolution grid</div>
        </motion.div>
      </section>

      {/* 4. THE OCEAN LAYERS (Sticky Interactive Story Scroll) */}
      <div ref={containerRef} className="relative w-full h-[400vh]">
        <div className="sticky top-0 w-full h-screen overflow-hidden flex items-center">
          
          {/* Layer 1: Surface (Left side text, Right side icon) */}
          <motion.div 
            className="absolute w-full h-full flex flex-col md:flex-row items-center px-6 md:px-[10%]"
            style={{ 
              opacity: l1Opacity, 
              pointerEvents: useTransform(l1Opacity, v => v > 0 ? "auto" : "none") 
            }}
          >
            <div className="w-full md:w-1/2 pr-0 md:pr-12 text-center md:text-left pt-20 md:pt-0">
              <motion.h2 style={{ y: l1Y }} className="text-[48px] md:text-[64px] font-medium tracking-[-0.04em] mb-6 text-[var(--color-aubergine-ink)] leading-[1.05]">
                Surface Telemetry
              </motion.h2>
              <motion.p style={{ y: l1Y }} className="text-[20px] md:text-[24px] text-[var(--color-aubergine-ink)]/75 font-light leading-relaxed">
                Real-time ingestion of sea surface temperature, altimetry, and wind vectors from operational satellites. Creating the massive data foundation required for continuous deep ocean reanalysis.
              </motion.p>
            </div>
            <div className="w-full md:w-1/2 flex justify-center items-center mt-12 md:mt-0">
              <motion.div style={{ y: l1Y, scale: l1Scale }}>
                <Waves size={280} strokeWidth={0.5} className="text-[var(--color-aubergine-ink)] opacity-10" />
              </motion.div>
            </div>
          </motion.div>

          {/* Layer 2: Engine (Left side icon, Right side text) */}
          <motion.div 
            className="absolute w-full h-full flex flex-col-reverse md:flex-row items-center px-6 md:px-[10%]"
            style={{ 
              opacity: l2Opacity, 
              pointerEvents: useTransform(l2Opacity, v => v > 0 ? "auto" : "none") 
            }}
          >
            <div className="w-full md:w-1/2 flex justify-center items-center mb-12 md:mb-0">
              <motion.div style={{ y: l2Y, scale: l2Scale }}>
                <Database size={280} strokeWidth={0.5} className="text-white opacity-10" />
              </motion.div>
            </div>
            <div className="w-full md:w-1/2 pl-0 md:pl-12 text-center md:text-left pt-20 md:pt-0">
              <motion.h2 style={{ y: l2Y }} className="text-[48px] md:text-[64px] font-medium tracking-[-0.04em] mb-6 text-white leading-[1.05]">
                ConvFormer Engine
              </motion.h2>
              <motion.p style={{ y: l2Y }} className="text-[20px] md:text-[24px] text-white/80 font-light leading-relaxed">
                A hybrid convolutional-transformer architecture processes spatial dependencies across the global grid. It maps complex surface signatures directly to dense, multi-variable subsurface layers.
              </motion.p>
            </div>
          </motion.div>

          {/* Layer 3: Output (Center text and icon) */}
          <motion.div 
            className="absolute w-full h-full flex flex-col items-center justify-center px-6 md:px-[10%]"
            style={{ 
              opacity: l3Opacity, 
              pointerEvents: useTransform(l3Opacity, v => v > 0 ? "auto" : "none") 
            }}
          >
            <motion.div style={{ y: l3Y, scale: l3Scale }} className="flex flex-col items-center text-center max-w-[800px]">
              <Anchor size={120} strokeWidth={0.5} className="text-white opacity-20 mb-10" />
              <h2 className="text-[48px] md:text-[72px] font-medium tracking-[-0.04em] mb-6 text-white leading-[1.05]">
                The Deep Ocean Output
              </h2>
              <p className="text-[20px] md:text-[26px] text-white/80 font-light leading-relaxed">
                High-resolution 3D temperature profiles accurately mapped across 15 standard depth layers. We resolve the global ocean column with unprecedented confidence down to 1000 meters.
              </p>
            </motion.div>
          </motion.div>

        </div>
      </div>

      {/* 5. FOOTER (Deepest layer, dark background) */}
      <footer className="w-full px-6 md:px-[60px] py-[80px] flex flex-col md:flex-row justify-between items-start md:items-center text-[14px] text-white/40 bg-[#0a192f] relative z-10 border-t border-white/5">
        <div className="flex items-center gap-2 font-medium text-white/70 mb-4 md:mb-0">
          <span>✱</span> OCEANEMBED
        </div>
        <div className="flex gap-8">
          <span>Status: Operational</span>
          <span>Copernicus Reanalysis</span>
        </div>
      </footer>

    </div>
  );
};

export default Landing;