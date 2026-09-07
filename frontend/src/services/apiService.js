const API_URL = "http://localhost:8000"

export async function getProfile(latitude, longitude) {
    const response = await fetch(
        `${API_URL}/predict/profile?latitude=${latitude}&longitude=${longitude}`
    )

    if (!response.ok) {
        throw new Error("Failed to fetch temperature profile")
    }

    return response.json()
}

export async function getSlice(depth) {
    const response = await fetch(
        `${API_URL}/predict/slice?depth_m=${depth}&date=latest`
    )

    if (!response.ok) {
        throw new Error("Failed to fetch temperature slice")
    }

    return response.json()
}