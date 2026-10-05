import { motion } from 'framer-motion'
import {
  ArrowRight, BarChart3, Brain, CheckCircle,
  Database, ShieldCheck, Sparkles, TrendingUp,
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar,
  LineChart, Line, PieChart, Pie, Cell,
  ResponsiveContainer, Tooltip,
} from 'recharts'

const mini = [
  { v: 12 }, { v: 22 }, { v: 18 }, { v: 31 },
  { v: 28 }, { v: 44 }, { v: 41 }, { v: 55 },
]
const pie = [
  { name: 'High',   value: 18 },
  { name: 'Medium', value: 30 },
  { name: 'Low',    value: 52 },
]
const FEATURES = [
  { icon: Brain,      title: 'XGBoost Algorithm',   desc: 'Industry-leading 94.2% prediction accuracy using gradient-boosted decision trees.' },
  { icon: BarChart3,  title: 'Advanced Analytics',   desc: 'Deep-dive dashboards with churn trends, revenue risk, and model performance metrics.' },
  { icon: ShieldCheck, title: 'AI Recommendations', desc: 'Segment-specific retention strategies generated automatically for each risk group.' },
  { icon: TrendingUp, title: 'Revenue Protection',   desc: 'Identify at-risk revenue early and act before customers churn.' },
]
const STATS = [
  { n: '94.2%', t: 'Model Accuracy' },
  { n: '25.4K+', t: 'Customers Analyzed' },
  { n: '18.01%', t: 'Churn Risk Rate' },
  { n: '$845K', t: 'Revenue at Risk' },
]

export default function Landing({ onLogin }) {
  const scrollTo = (id) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="ai-bg min-h-screen">
      {/* Nav */}
      <nav className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
        <div
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="flex items-center gap-3 cursor-pointer"
        >
          <div className="w-10 h-10 rounded-xl glow-btn flex items-center justify-center">
            <ShieldCheck size={20} />
          </div>
          <span className="font-bold text-lg">ChurnShield AI</span>
        </div>
        <div className="hidden md:flex gap-8 text-sm text-slate-300">
          {[
            { label: 'Home', action: () => window.scrollTo({ top: 0, behavior: 'smooth' }) },
            { label: 'Features', action: () => scrollTo('features') },
            { label: 'How It Works', action: () => scrollTo('how-it-works') },
            { label: 'Pricing', action: () => scrollTo('pricing') },
            { label: 'Contact', action: () => scrollTo('contact') },
          ].map((item) => (
            <span
              key={item.label}
              onClick={item.action}
              className="cursor-pointer hover:text-white transition-colors"
            >
              {item.label}
            </span>
          ))}
        </div>
        <button onClick={onLogin} className="glow-btn px-5 py-2 rounded-lg text-sm font-semibold">
          Get Started
        </button>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 py-12 lg:py-20 grid lg:grid-cols-2 gap-12 items-center">
        <motion.div initial={{ opacity: 0, x: -40 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}>
          <div className="inline-flex gap-2 items-center glass rounded-full px-4 py-2 text-sm mb-6">
            <Sparkles size={15} className="text-cyan-300" />
            <span className="text-slate-300">XGBoost Powered E-Commerce Intelligence</span>
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold leading-tight">
            Autonomous Retention{' '}
            <span className="text-cyan-300">with Human-in-the-Loop</span>{' '}
            Safety Controls
          </h1>
          <p className="text-slate-300 mt-6 text-lg leading-relaxed max-w-xl">
            Securely execute retention campaigns with real-time safety validations,
            Sentinel-based auto-healing, and cryptographic proof of operator review decisions.
          </p>
          <div className="flex flex-wrap gap-4 mt-8">
            <button
              onClick={onLogin}
              className="glow-btn px-8 py-3 rounded-xl font-semibold flex items-center gap-2"
            >
              Get Started <ArrowRight size={18} />
            </button>
            <button
              onClick={onLogin}
              className="glass px-8 py-3 rounded-xl font-semibold hover:bg-white/10 transition"
            >
              View Dashboard
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-5 mt-12">
            {STATS.map(({ n, t }) => (
              <div key={t}>
                <h3 className="text-cyan-300 font-bold text-2xl">{n}</h3>
                <p className="text-xs text-slate-400 mt-1">{t}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Floating charts */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7 }}
          className="relative min-h-[480px] hidden lg:block"
        >
          <div className="absolute inset-0 rounded-full bg-blue-500/8 blur-3xl" />
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full border border-blue-400/20 flex items-center justify-center">
            <Brain className="text-cyan-300/40" size={100} />
          </div>

          <FloatCard
            className="left-0 top-8" title="Churn Risk" value="18.01%"
            delay={0}
          >
            <ResponsiveContainer width="100%" height={70}>
              <AreaChart data={mini}>
                <Tooltip contentStyle={{ background: '#0c1427', border: 'none', fontSize: 11 }} />
                <Area dataKey="v" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </FloatCard>

          <FloatCard
            className="right-0 top-8" title="Revenue at Risk" value="$845,000"
            delay={0.5}
          >
            <ResponsiveContainer width="100%" height={70}>
              <BarChart data={mini}>
                <Tooltip contentStyle={{ background: '#0c1427', border: 'none', fontSize: 11 }} />
                <Bar dataKey="v" fill="#6d5dfc" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </FloatCard>

          <FloatCard
            className="left-0 bottom-16" title="Total Customers" value="25,430"
            delay={1}
          >
            <ResponsiveContainer width="100%" height={70}>
              <LineChart data={mini}>
                <Tooltip contentStyle={{ background: '#0c1427', border: 'none', fontSize: 11 }} />
                <Line dataKey="v" stroke="#19c37d" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </FloatCard>

          <FloatCard
            className="right-0 bottom-16" title="Risk Breakdown" value="XGBoost"
            delay={1.5}
          >
            <ResponsiveContainer width="100%" height={70}>
              <PieChart>
                <Pie data={pie} dataKey="value" innerRadius={20} outerRadius={33}>
                  {pie.map((_, i) => (
                    <Cell key={i} fill={['#ff465c', '#ffb020', '#19c37d'][i]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0c1427', border: 'none', fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </FloatCard>
        </motion.div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-white/10 glass">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 lg:grid-cols-4 gap-0">
          {FEATURES.map(({ icon: Icon, title, desc }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="p-8 border-b md:border-b-0 md:border-r border-white/10 last:border-0"
            >
              <div className="w-12 h-12 rounded-xl glow-btn flex items-center justify-center mb-5">
                <Icon size={22} />
              </div>
              <h3 className="font-bold text-lg mb-2">{title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-6">
          {[
            { step: '01', title: 'Upload Dataset', desc: 'Upload your customer CSV or Excel file with purchase history and behaviour data.' },
            { step: '02', title: 'AI Analysis',    desc: 'Our XGBoost model analyses 9 key features to predict each customer\'s churn probability.' },
            { step: '03', title: 'Risk Scoring',   desc: 'Customers are segmented into High, Medium, and Low risk groups automatically.' },
            { step: '04', title: 'Take Action',    desc: 'Receive AI-generated retention recommendations tailored to each risk segment.' },
          ].map(({ step, title, desc }) => (
            <div key={step} className="glass rounded-2xl p-6 card-3d text-center">
              <div className="text-5xl font-black text-cyan-300/30 mb-4">{step}</div>
              <h3 className="font-bold text-lg mb-3">{title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>
      {/* Pricing Section */}
      <section id="pricing" className="border-t border-white/10 glass py-16">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-4">Transparent Enterprise Pricing</h2>
          <p className="text-slate-400 text-sm text-center mb-12 max-w-lg mx-auto">
            Scale your customer retention with secure, robust machine-learning analytics.
          </p>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              { name: 'Starter', price: '$119', desc: 'Ideal for growing ecommerce sites.', features: ['10,000 customers analyzed', 'XGBoost churn risk prediction', 'Email alerts', 'Standard CSV uploads'] },
              { name: 'Pro', price: '$299', desc: 'For established brands needing automation.', features: ['50,000 customers analyzed', 'Automated campaign triggers', 'Human-in-the-loop safety review', '24/7 client portal access'], popular: true },
              { name: 'Enterprise', price: 'Custom', desc: 'For high-scale institutional operations.', features: ['Unlimited customer records', 'Secure Enclave machine signature', 'Custom model fine-tuning', 'Dedicated system support'] },
            ].map((plan) => (
              <div key={plan.name} className={`glass rounded-3xl p-8 border flex flex-col relative card-3d ${plan.popular ? 'border-cyan-500/40 shadow-lg shadow-cyan-950/20' : 'border-white/10'}`}>
                {plan.popular && (
                  <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 badge bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-[10px] uppercase font-bold tracking-wider py-1 px-3">
                    Most Popular
                  </span>
                )}
                <h3 className="font-bold text-xl">{plan.name}</h3>
                <p className="text-xs text-slate-400 mt-2 min-h-[32px]">{plan.desc}</p>
                <div className="my-6">
                  <span className="text-3xl font-black text-white">{plan.price}</span>
                  {plan.price !== 'Custom' && <span className="text-slate-400 text-sm font-normal"> /mo</span>}
                </div>
                <ul className="space-y-3 text-sm text-slate-300 flex-1 mb-8">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2">
                      <CheckCircle size={14} className="text-cyan-300 shrink-0" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <button onClick={onLogin} className={`w-full py-3 rounded-xl font-semibold text-sm transition-all ${plan.popular ? 'glow-btn' : 'glass hover:bg-white/10'}`}>
                  {plan.price === 'Custom' ? 'Contact Sales' : 'Get Started'}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="max-w-7xl mx-auto px-6 py-16 border-t border-white/10">
        <div className="grid lg:grid-cols-2 gap-12 items-center max-w-5xl mx-auto">
          <div>
            <h2 className="text-3xl font-bold mb-4">Contact Our Security Team</h2>
            <p className="text-slate-400 text-sm leading-relaxed mb-6">
              Have questions about Secure Enclave machine signatures, data isolation, or custom model integrations? Send us a message and our security architects will get back to you.
            </p>
            <div className="space-y-3 font-mono text-xs text-slate-300">
              <p>📍 Location: Xoras Systems, Mac M4 Dojo Grid</p>
              <p>📧 Email: <a href="mailto:support@churnshield.ai" className="text-cyan-300 hover:underline">support@churnshield.ai</a></p>
              <p>🛡️ Security Portal: <span className="text-emerald-400">NOMINAL // SECURED</span></p>
            </div>
          </div>
          <div className="glass rounded-3xl p-6 border border-white/10 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] text-slate-400 mb-1.5 block uppercase tracking-wider font-mono">Name</label>
                <input className="input text-xs" placeholder="Your name" />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 mb-1.5 block uppercase tracking-wider font-mono">Email</label>
                <input className="input text-xs" placeholder="your@email.com" />
              </div>
            </div>
            <div>
              <label className="text-[10px] text-slate-400 mb-1.5 block uppercase tracking-wider font-mono">Message</label>
              <textarea className="input text-xs h-24 resize-none" placeholder="How can our security team help you?" />
            </div>
            <button onClick={() => alert('Message sent successfully! Our security team will contact you.')} className="glow-btn w-full py-3 rounded-xl text-xs font-bold">
              Send Secure Message
            </button>
          </div>
        </div>
      </section>
      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 pb-20 text-center">
        <div className="glass rounded-3xl p-12 card-3d">
          <CheckCircle size={48} className="text-cyan-300 mx-auto mb-6" />
          <h2 className="text-3xl font-bold mb-4">Ready to Reduce Customer Churn?</h2>
          <p className="text-slate-300 mb-8 max-w-xl mx-auto">
            Join e-commerce businesses using ChurnShield AI to retain customers and protect revenue.
          </p>
          <button
            onClick={onLogin}
            className="glow-btn px-10 py-4 rounded-xl font-semibold text-lg inline-flex items-center gap-2"
          >
            Start Live Dashboard <ArrowRight size={20} />
          </button>
          <p className="text-slate-400 text-sm mt-4">Secure administrator authentication required</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 glass">
        <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg glow-btn flex items-center justify-center">
              <ShieldCheck size={16} />
            </div>
            <span className="font-bold text-sm">ChurnShield AI</span>
          </div>
          <p className="text-slate-400 text-xs">© 2025 ChurnShield AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

function FloatCard({ className, title, value, delay, children }) {
  return (
    <motion.div
      animate={{ y: [0, -12, 0] }}
      transition={{ duration: 4, repeat: Infinity, delay }}
      className={`absolute ${className} glass rounded-2xl p-4 w-52 card-3d`}
    >
      <p className="text-slate-400 text-xs">{title}</p>
      <h3 className="text-xl font-bold text-white mt-1 mb-3">{value}</h3>
      {children}
    </motion.div>
  )
}
