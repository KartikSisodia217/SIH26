import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts"

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

    return (
        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950 p-4">
            <h3 className="mb-4 text-sm font-semibold text-white">
                Temperature Profile
            </h3>

            {location && (
                <p className="mb-3 text-xs text-slate-400">
                    {location.latitude.toFixed(2)}°N,{" "}
                    {location.longitude.toFixed(2)}°E
                </p>
            )}

            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />

                        <XAxis
                            dataKey="depth"
                            label={{
                                value: "Depth (m)",
                                position: "insideBottom",
                                offset: -5,
                            }}
                        />

                        <YAxis
                            label={{
                                value: "Temperature (°C)",
                                angle: -90,
                                position: "insideLeft",
                            }}
                        />

                        <Tooltip />

                        <Line
                            type="monotone"
                            dataKey="temperature"
                            stroke="#22d3ee"
                            strokeWidth={2}
                            dot={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}

export default ProfileChart