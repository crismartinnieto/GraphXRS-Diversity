import React, { useState } from 'react';
import { BarChart, Bar, LineChart, Line, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { Upload, TrendingUp, Users, Filter, BarChart3, Activity, Eye, Layers, GitBranch, Target, Zap, Award } from 'lucide-react';

const MetricsVisualizer = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [usuarioSeleccionado, setUsuarioSeleccionado] = useState(null);
  const [metricasCaminos, setMetricasCaminos] = useState([]);
  const [metricasGlobales, setMetricasGlobales] = useState([]);
  const [metricasEjemplo, setMetricasEjemplo] = useState([]);
  const [metricasPropiedad, setMetricasPropiedad] = useState([]);
  const [filtroHotel, setFiltroHotel] = useState('');
  const [vistaActual, setVistaActual] = useState('global');
  const [isLoading, setIsLoading] = useState(false);

  const handleFileUpload = async (event) => {
    setIsLoading(true);
    const files = Array.from(event.target.files);
    
    for (const file of files) {
      const text = await file.text();
      const lines = text.split('\n');
      const headers = lines[0].split(',').map(h => h.trim());
      
      const data = lines.slice(1)
        .filter(line => line.trim())
        .map(line => {
          const values = line.split(',');
          const obj = {};
          headers.forEach((header, i) => {
            const value = values[i]?.trim();
            obj[header] = isNaN(value) ? value : parseFloat(value);
          });
          return obj;
        });

      const match = file.webkitRelativePath.match(/metricas_usuario_(\d+)/);
      const userId = match ? match[1] : data[0]?.usuario?.toString();

      if (userId && !usuarios.includes(userId)) {
        setUsuarios(prev => {
          if (!prev.includes(userId)) {
            return [...prev, userId].sort();
          }
          return prev;
        });
      }
      if (file.name.includes('metricas_caminos')) {
        setMetricasCaminos(prev => {
          const filtered = prev.filter(m => m.usuario !== userId);
          return [...filtered, { usuario: userId, data }];
        });
      } else if (file.name.includes('metricas_globales')) {
        setMetricasGlobales(prev => {
          const filtered = prev.filter(m => m.usuario !== userId);
          return [...filtered, { usuario: userId, data }];
        });
      } else if (file.name.includes('metricas_nivel_ejemplo')) {
        setMetricasEjemplo(prev => {
          const filtered = prev.filter(m => m.usuario !== userId);
          return [...filtered, { usuario: userId, data }];
        });
      } else if (file.name.includes('metricas_nivel_propiedad')) {
        setMetricasPropiedad(prev => {
          const filtered = prev.filter(m => m.usuario !== userId);
          return [...filtered, { usuario: userId, data }];
        });
      }
    }
    
    setTimeout(() => setIsLoading(false), 500);
  };

  const getDatosUsuario = (tipo) => {
    const mapa = {
      'caminos': metricasCaminos,
      'globales': metricasGlobales,
      'ejemplo': metricasEjemplo,
      'propiedad': metricasPropiedad
    };
    return mapa[tipo]?.find(m => m.usuario === usuarioSeleccionado)?.data || [];
  };

  const getHotelesFiltrados = (datos) => {
    if (!filtroHotel) return datos;
    return datos.filter(d => 
      d.hotel_recomendado?.toString().includes(filtroHotel) ||
      d.hotel_consumido?.toString().includes(filtroHotel)
    );
  };

  const MetricCard = ({ label, value, icon: Icon, color, trend }) => (
    <div className="metric-card">
      <div className="metric-card-content">
        <div className="metric-info">
          <p className="metric-label">{label}</p>
          <p className="metric-value">{value}%</p>
          {trend && (
            <p className="metric-trend">
              <TrendingUp size={14} />
              {trend}
            </p>
          )}
        </div>
        <div className={`metric-icon ${color}`}>
          <Icon className="icon-white" size={28} />
        </div>
      </div>
    </div>
  );
  const renderMetricasGlobales = () => {
    const datos = getDatosUsuario('globales');
    if (!datos.length) return (
      <div className="empty-state">
        <Eye size={64} className="empty-icon" />
        <p>No hay datos disponibles</p>
      </div>
    );

    const top10 = datos
      .sort((a, b) => b.novelty_ratio - a.novelty_ratio)
      .slice(0, 10)
      .map(d => ({
        hotel: `Hotel ${d.hotel_recomendado}`,
        novelty: parseFloat((d.novelty_ratio * 100).toFixed(1)),
        surprise: parseFloat((d.surprise_score * 100).toFixed(1)),
        coverage: parseFloat((d.preference_coverage * 100).toFixed(1))
      }));

    const promedios = {
      novelty: (datos.reduce((s, d) => s + d.novelty_ratio, 0) / datos.length * 100).toFixed(1),
      surprise: (datos.reduce((s, d) => s + d.surprise_score, 0) / datos.length * 100).toFixed(1),
      prefCoverage: (datos.reduce((s, d) => s + d.preference_coverage, 0) / datos.length * 100).toFixed(1),
      blindSpot: (datos.reduce((s, d) => s + d.blind_spot_coverage, 0) / datos.length * 100).toFixed(1)
    };

    const radarData = [
      { metric: 'Novelty', value: parseFloat(promedios.novelty) },
      { metric: 'Surprise', value: parseFloat(promedios.surprise) },
      { metric: 'Coverage', value: parseFloat(promedios.prefCoverage) },
      { metric: 'Blind Spot', value: parseFloat(promedios.blindSpot) }
    ];

    return (
      <div className="metrics-section">
        <div className="metrics-grid">
          <MetricCard 
            label="Novelty Promedio" 
            value={promedios.novelty} 
            icon={Zap} 
            color="bg-blue"
            trend="+5.2% vs promedio"
          />
          <MetricCard 
            label="Surprise Score" 
            value={promedios.surprise} 
            icon={Activity} 
            color="bg-purple"
            trend="+3.8% vs promedio"
          />
          <MetricCard 
            label="Preference Coverage" 
            value={promedios.prefCoverage} 
            icon={Target} 
            color="bg-green"
            trend="+2.1% vs promedio"
          />
          <MetricCard 
            label="Blind Spot Coverage" 
            value={promedios.blindSpot} 
            icon={Eye} 
            color="bg-orange"
            trend="+4.5% vs promedio"
          />
        </div>

        <div className="charts-grid">
          <div className="chart-card">
            <div className="chart-header">
              <div className="chart-icon bg-purple-light">
                <Award className="text-purple" size={24} />
              </div>
              <h3>Perfil de Métricas</h3>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#6b7280', fontSize: 14 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#9ca3af' }} />
                <Radar name="Métricas" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <div className="chart-header">
              <div className="chart-icon bg-blue-light">
                <BarChart3 className="text-blue" size={24} />
              </div>
              <h3>Top 10 Hoteles por Novelty</h3>
            </div>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={top10}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis 
                  dataKey="hotel" 
                  angle={-45} 
                  textAnchor="end" 
                  height={100}
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                />
                <YAxis tick={{ fill: '#6b7280' }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: 'none', 
                    borderRadius: '8px', 
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)' 
                  }} 
                />
                <Legend />
                <Bar dataKey="novelty" fill="#3b82f6" name="Novelty %" radius={[8, 8, 0, 0]} />
                <Bar dataKey="surprise" fill="#8b5cf6" name="Surprise %" radius={[8, 8, 0, 0]} />
                <Bar dataKey="coverage" fill="#10b981" name="Coverage %" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  const renderMetricasCaminos = () => {
    const datos = getHotelesFiltrados(getDatosUsuario('caminos'));
    if (!datos.length) return (
      <div className="empty-state">
        <GitBranch size={64} className="empty-icon" />
        <p>No hay datos de caminos disponibles</p>
      </div>
    );

    const porHotel = {};
    datos.forEach(d => {
      const key = d.hotel_recomendado;
      if (!porHotel[key]) {
        porHotel[key] = {
          hotel: `Hotel ${key}`,
          path_length: 0,
          path_count: 0,
          path_confidence: 0,
          count: 0
        };
      }
      porHotel[key].path_length += d.path_length || 0;
      porHotel[key].path_count += d.path_count || 0;
      porHotel[key].path_confidence += d.path_confidence_score || 0;
      porHotel[key].count++;
    });

    const agregado = Object.values(porHotel)
      .map(h => ({
        ...h,
        path_length: parseFloat((h.path_length / h.count).toFixed(2)),
        path_count: parseFloat((h.path_count / h.count).toFixed(2)),
        path_confidence: parseFloat((h.path_confidence / h.count).toFixed(2))
      }))
      .sort((a, b) => b.path_confidence - a.path_confidence)
      .slice(0, 15);

    return (
      <div className="metrics-section">
        <div className="chart-card">
          <div className="chart-header">
            <div className="chart-icon bg-indigo-light">
              <GitBranch className="text-indigo" size={24} />
            </div>
            <h3>Análisis de Caminos de Recomendación</h3>
          </div>
          <ResponsiveContainer width="100%" height={450}>
            <LineChart data={agregado}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis 
                dataKey="hotel" 
                angle={-45} 
                textAnchor="end" 
                height={100}
                tick={{ fill: '#6b7280', fontSize: 12 }}
              />
              <YAxis yAxisId="left" tick={{ fill: '#6b7280' }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#6b7280' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: 'none', 
                  borderRadius: '8px', 
                  boxShadow: '0 4px 6px rgba(0,0,0,0.1)' 
                }} 
              />
              <Legend />
              <Line 
                yAxisId="left" 
                type="monotone" 
                dataKey="path_length" 
                stroke="#3b82f6" 
                name="Path Length" 
                strokeWidth={3}
                dot={{ fill: '#3b82f6', r: 4 }}
              />
              <Line 
                yAxisId="left" 
                type="monotone" 
                dataKey="path_count" 
                stroke="#10b981" 
                name="Path Count" 
                strokeWidth={3}
                dot={{ fill: '#10b981', r: 4 }}
              />
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="path_confidence" 
                stroke="#f59e0b" 
                name="Confidence" 
                strokeWidth={3}
                dot={{ fill: '#f59e0b', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };
  const renderMetricasEjemplo = () => {
    const datos = getHotelesFiltrados(getDatosUsuario('ejemplo'));
    if (!datos.length) return (
      <div className="empty-state">
        <Layers size={64} className="empty-icon" />
        <p>No hay datos de ejemplos disponibles</p>
      </div>
    );

    const scatter = datos.map(d => ({
      similarity: parseFloat((d.example_similarity_score * 100).toFixed(1)),
      consensus: parseFloat((d.example_consensus_score || 0).toFixed(2)),
      hotel: d.hotel_recomendado
    })).slice(0, 100);

    const top10Similarity = [...datos]
      .sort((a, b) => b.example_similarity_score - a.example_similarity_score)
      .slice(0, 10)
      .map(d => ({
        hotel: `H${d.hotel_recomendado}`,
        similarity: parseFloat((d.example_similarity_score * 100).toFixed(1)),
        consensus: parseFloat((d.example_consensus_score || 0).toFixed(2)),
        coverage: parseFloat((d.example_coverage * 100).toFixed(1))
      }));

    return (
      <div className="metrics-section">
        <div className="charts-grid">
          <div className="chart-card">
            <div className="chart-header">
              <div className="chart-icon bg-purple-light">
                <Activity className="text-purple" size={24} />
              </div>
              <h3>Similarity vs Consensus</h3>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis 
                  dataKey="similarity" 
                  name="Similarity %" 
                  tick={{ fill: '#6b7280' }}
                  label={{ value: 'Similarity %', position: 'bottom', fill: '#6b7280' }}
                />
                <YAxis 
                  dataKey="consensus" 
                  name="Consensus" 
                  tick={{ fill: '#6b7280' }}
                  label={{ value: 'Consensus', angle: -90, position: 'left', fill: '#6b7280' }}
                />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: 'none', 
                    borderRadius: '8px', 
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)' 
                  }}
                />
                <Scatter data={scatter} fill="#8b5cf6" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <div className="chart-header">
              <div className="chart-icon bg-blue-light">
                <Award className="text-blue" size={24} />
              </div>
              <h3>Top 10 por Similarity</h3>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={top10Similarity}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="hotel" tick={{ fill: '#6b7280' }} />
                <YAxis tick={{ fill: '#6b7280' }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: 'none', 
                    borderRadius: '8px', 
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)' 
                  }}
                />
                <Legend />
                <Bar dataKey="similarity" fill="#3b82f6" name="Similarity %" radius={[8, 8, 0, 0]} />
                <Bar dataKey="consensus" fill="#10b981" name="Consensus" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  const renderMetricasPropiedad = () => {
    const datos = getDatosUsuario('propiedad');
    if (!datos.length) return (
      <div className="empty-state">
        <Filter size={64} className="empty-icon" />
        <p>No hay datos de propiedades disponibles</p>
      </div>
    );

    const topProps = [...datos]
      .sort((a, b) => b.pagerank - a.pagerank)
      .slice(0, 10)
      .map(d => ({
        propiedad: (d.propiedad?.substring(0, 25) || 'Unknown') + '...',
        pagerank: parseFloat((d.pagerank * 1000).toFixed(2)),
        betweenness: parseFloat((d.betweenness_centrality * 100).toFixed(2)),
        degree: d.degree_centrality || 0
      }));

    const popSpec = datos
      .filter(d => d.attribute_popularity > 0)
      .map(d => ({
        popularity: d.attribute_popularity,
        specificity: d.attribute_specificity,
        propiedad: d.propiedad?.substring(0, 20) || 'Unknown'
      }))
      .slice(0, 50);

    return (
      <div className="metrics-section">
        <div className="charts-grid">
          <div className="chart-card">
            <div className="chart-header">
              <div className="chart-icon bg-green-light">
                <Target className="text-green" size={24} />
              </div>
              <h3>Top Propiedades PageRank</h3>
            </div>
            <ResponsiveContainer width="100%" height={450}>
              <BarChart data={topProps} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis type="number" tick={{ fill: '#6b7280' }} />
                <YAxis dataKey="propiedad" type="category" width={150} tick={{ fill: '#6b7280', fontSize: 11 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: 'none', 
                    borderRadius: '8px', 
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)' 
                  }}
                />
                <Legend />
                <Bar dataKey="pagerank" fill="#3b82f6" name="PageRank (×1000)" radius={[0, 8, 8, 0]} />
                <Bar dataKey="betweenness" fill="#10b981" name="Betweenness (×100)" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <div className="chart-header">
              <div className="chart-icon bg-orange-light">
                <Activity className="text-orange" size={24} />
              </div>
              <h3>Popularidad vs Especificidad</h3>
            </div>
            <ResponsiveContainer width="100%" height={450}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis 
                  dataKey="popularity" 
                  name="Popularity" 
                  tick={{ fill: '#6b7280' }}
                  label={{ value: 'Popularidad', position: 'bottom', fill: '#6b7280' }}
                />
                <YAxis 
                  dataKey="specificity" 
                  name="Specificity" 
                  tick={{ fill: '#6b7280' }}
                  label={{ value: 'Especificidad', angle: -90, position: 'left', fill: '#6b7280' }}
                />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: 'none', 
                    borderRadius: '8px', 
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)' 
                  }}
                />
                <Scatter data={popSpec} fill="#f59e0b" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };
  return (
    <div className="app-container">
      <div className="content-wrapper">
        <div className="header-gradient">
          <div className="header-overlay"></div>
          <div className="header-content">
            <div className="header-icon-wrapper">
              <div className="header-icon-bg">
                <BarChart3 className="header-icon" size={36} />
              </div>
              <h1 className="header-title">
                Visualizador de Métricas XAI
              </h1>
            </div>
            <p className="header-subtitle">
              Sistema de Recomendación Explicable - Análisis Avanzado de Métricas
            </p>
          </div>
        </div>

        {usuarios.length === 0 ? (
          <div className="upload-container">
            <div className="upload-content">
              <div className="upload-icon-wrapper">
                <Upload className="upload-icon" size={64} />
              </div>
              <h2 className="upload-title">Cargar Datos de Métricas</h2>
              <p className="upload-description">
                Selecciona la carpeta que contiene las subcarpetas <span className="code-text">metricas_usuario_X</span> para comenzar el análisis
              </p>
              <label className="upload-label">
                <input
                  type="file"
                  webkitdirectory="true"
                  directory="true"
                  multiple
                  onChange={handleFileUpload}
                  className="upload-input"
                />
                <div className="upload-button">
                  <div className="upload-button-content">
                    <Upload size={20} />
                    Seleccionar Carpeta
                  </div>
                </div>
              </label>
            </div>
          </div>
        ) : (
          <div className="main-content">
            <div className="user-selection-card">
              <div className="section-header">
                <div className="section-icon-wrapper bg-blue-light">
                  <Users className="text-blue" size={24} />
                </div>
                <h2 className="section-title">Seleccionar Usuario</h2>
              </div>
              <div className="user-buttons">
                {usuarios.map(u => (
                  <button
                    key={u}
                    onClick={() => setUsuarioSeleccionado(u)}
                    className={`user-button ${usuarioSeleccionado === u ? 'user-button-active' : 'user-button-inactive'}`}
                  >
                    Usuario {u}
                  </button>
                ))}
              </div>
            </div>

            {usuarioSeleccionado && (
              <>
                <div className="filters-card">
                  <div className="filters-content">
                    <div className="view-tabs">
                      {[
                        { id: 'global', label: 'Métricas Globales', icon: BarChart3 },
                        { id: 'caminos', label: 'Caminos', icon: GitBranch },
                        { id: 'ejemplo', label: 'Ejemplos', icon: Layers },
                        { id: 'propiedad', label: 'Propiedades', icon: Filter }
                      ].map(vista => (
                        <button
                          key={vista.id}
                          onClick={() => setVistaActual(vista.id)}
                          className={`view-tab ${vistaActual === vista.id ? 'view-tab-active' : 'view-tab-inactive'}`}
                        >
                          <vista.icon size={18} />
                          {vista.label}
                        </button>
                      ))}
                    </div>
                    <input
                      type="text"
                      placeholder="Filtrar por hotel..."
                      value={filtroHotel}
                      onChange={(e) => setFiltroHotel(e.target.value)}
                      className="filter-input"
                    />
                  </div>
                </div>

                <div className="visualization-area">
                  {vistaActual === 'global' && renderMetricasGlobales()}
                  {vistaActual === 'caminos' && renderMetricasCaminos()}
                  {vistaActual === 'ejemplo' && renderMetricasEjemplo()}
                  {vistaActual === 'propiedad' && renderMetricasPropiedad()}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricsVisualizer;