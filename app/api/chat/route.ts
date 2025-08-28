import { NextRequest, NextResponse } from 'next/server'

interface ChatRequest {
  message: string
}

interface ChatResponse {
  response: string
  timestamp: string
}

export async function POST(request: NextRequest) {
  try {
    const body: ChatRequest = await request.json()
    
    if (!body.message || typeof body.message !== 'string') {
      return NextResponse.json(
        { error: 'Invalid message' },
        { status: 400 }
      )
    }

    // Call the external API
    const apiResponse = await fetch('https://ideally-guided-moose.ngrok-free.app/run-agent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: body.message
      })
    })

    if (!apiResponse.ok) {
      throw new Error(`API responded with status: ${apiResponse.status}`)
    }

    const apiData = await apiResponse.json()
    
    // Assuming the API returns the response in a specific format
    // Adjust this based on the actual API response structure
    const chatResponse: ChatResponse = {
      response: apiData.response || apiData.message || JSON.stringify(apiData),
      timestamp: new Date().toISOString()
    }

    return NextResponse.json(chatResponse)
  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}