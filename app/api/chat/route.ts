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

    // Fake responses based on keywords in the message
    let response = "That's a great question about daily fantasy sports!"
    
    const message = body.message.toLowerCase()
    
    if (message.includes('player') || message.includes('lineup')) {
      response = "Based on current projections, here are some key players to consider: Patrick Mahomes (QB) has a great matchup this week with high upside. Christian McCaffrey (RB) continues to dominate touches. Consider stacking with their respective pass catchers for tournament plays."
    } else if (message.includes('strategy') || message.includes('tips')) {
      response = "For optimal DFS strategy this week: 1) Target games with high over/unders (50+ points), 2) Look for value plays in the $4,500-$5,500 range, 3) Consider game stacking in tournaments, 4) Pay attention to late injury reports for pivot opportunities."
    } else if (message.includes('injury') || message.includes('status')) {
      response = "Key injury updates: Monitor the status of these players before lock - they could significantly impact lineup decisions. Always check official injury reports 30 minutes before game time and have backup pivots ready."
    } else if (message.includes('weather')) {
      response = "Weather can significantly impact DFS scoring. Wind speeds over 15 mph affect passing games. Rain/snow favors running backs. Dome games provide the most consistent scoring environments."
    } else if (message.includes('stack') || message.includes('correlation')) {
      response = "Game stacking is crucial for GPP success. Popular stacks include: QB + WR1 + Opposing WR1, QB + TE + Defense, or full game stacks with 4-5 players from a shootout game. Focus on games with 50+ point totals."
    } else {
      response = "I can help you with player projections, lineup optimization, injury analysis, weather impacts, and DFS strategy. What specific aspect of daily fantasy sports would you like to explore?"
    }

    const chatResponse: ChatResponse = {
      response,
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