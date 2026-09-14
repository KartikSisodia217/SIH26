import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
function ProfileChart({ location, profileData }) {
    const mockData = [
        { depth: 0, temperature: 28.4 },
        { depth: 5, temperature: 28.1 },
        { depth: 10, temperature: 27.8 },
        { depth: 20, temperature: 27.3 },
        { depth: 30, temperature: 26.8 },
        { depth: 50, temperature: 26.1 },
        { depth: 75, temperature: 25.4 },
        { depth: 100, temperature: 24.7 },
        { depth: 125, temperature: 23.9 },
        { depth: 150, temperature: 22.8 },
        { depth: 200, temperature: 20.6 },
        { depth: 300, temperature: 17.1 },
        { depth: 500, temperature: 12.8 },
        { depth: 700, temperature: 9.4 },
        { depth: 1000, temperature: 7.1 },
    ]
    const data = profileData?.depths?.map((depth, index) => ({
        depth,
        temperature: profileData.temperatures[index],
    })) ?? mockData

    const targetDepths = [0, 50, 100, 150, 200, 300, 500, 700, 1000]
    const tableData = data.filter(d => targetDepths.includes(d.depth))

    return (
        <div className="rounded-[24px] border border-black/5 bg-white shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-8 flex flex-col">
            <div className="flex justify-between items-end mb-6">
                <h3 className="text-[11px] uppercase tracking-widest text-[#1b0624]/40 font-medium">
                    Vertical Profile
                </h3>
                {location && (
                    <p className="text-[13px] font-mono text-[#1b0624]/40">
                        {location.latitude.toFixed(2)}°, {location.longitude.toFixed(2)}°
                    </p>
                )}
            </div>

            <div className="h-48 mb-8">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" horizontal={true} vertical={false} />
                        
                        <XAxis
                            type="number"
                            dataKey="depth"
                            stroke="rgba(0,0,0,0.1)"
                            tick={{ fill: 'rgba(27,6,36,0.4)', fontSize: 11, fontFamily: 'monospace' }}
                            tickLine={false}
                            axisLine={false}
                        />

                        <YAxis
                            type="number"
                            dataKey="temperature"
                            stroke="rgba(0,0,0,0.1)"
                            tick={{ fill: 'rgba(27,6,36,0.4)', fontSize: 11, fontFamily: 'monospace' }}
                            tickLine={false}
                            axisLine={false}
                            domain={['dataMin - 1', 'dataMax + 1']}
                        />

                        <Tooltip 
                            contentStyle={{ backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.05)', borderRadius: '12px', fontSize: '12px', boxShadow: '0 4px 24px rgba(0,0,0,0.06)' }}
                            itemStyle={{ color: '#1b0624' }}
                            formatter={(value, name) => [value + '°C', name === 'temperature' ? 'Temperature' : name]}
                            labelFormatter={(label) => 'Depth: ' + label + 'm'}
                        />

                        <Line
                            type="monotone"
                            dataKey="temperature"
                            stroke="#1b0624"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 4, fill: '#1b0624', stroke: '#fff', strokeWidth: 2 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            <div>
                <h4 className="text-[11px] uppercase tracking-widest text-[#1b0624]/40 font-medium mb-3">
                    Temperature by Depth
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-2">
                    {tableData.map((row) => (
                        <div key={row.depth} className="flex justify-between items-center text-[12px] font-mono border-b border-black/5 py-1">
                            <span className="text-[#1b0624]/50">{row.depth}m</span>
                            <span className="text-[#1b0624] font-medium">{row.temperature.toFixed(1)}°C</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
export default ProfileChart