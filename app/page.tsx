"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Send, Zap, TrendingUp } from "lucide-react"

interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
}

export default function DailyFantasySavant() {
  const [messages, setMessages] = useState<Message[]>([])
  
  useEffect(() => {
    setMessages([
      {
        id: "1",
        content:
          "Welcome to Daily Fantasy Savant! I'm your AI assistant for all things daily fantasy sports. Ask me about player projections, lineup strategies, or any DFS questions you have!",
        isUser: false,
        timestamp: new Date(),
      },
    ])
  }, [])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      isUser: true,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: inputValue }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        isUser: false,
        timestamp: new Date(data.timestamp),
      }
      
      setMessages((prev) => [...prev, aiResponse])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "Sorry, I encountered an error processing your request. Please try again.",
        isUser: false,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card to-background relative overflow-hidden">
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-3/4 left-1/2 w-64 h-64 bg-secondary/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      <div className="relative z-10 flex flex-col h-screen max-w-4xl mx-auto">
        <header className="p-6 text-center border-b border-border/50 backdrop-blur-sm">
          <div className="flex items-center justify-center gap-3 mb-2">
            <div className="p-2 rounded-full bg-primary/20 shadow-lg shadow-primary/25">
              <Zap className="w-8 h-8 text-primary animate-pulse" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent animate-pulse">
              Daily Fantasy Savant
            </h1>
            <div className="p-2 rounded-full bg-accent/20 shadow-lg shadow-accent/25">
              <TrendingUp className="w-8 h-8 text-accent animate-pulse" />
            </div>
          </div>
          <p className="text-muted-foreground text-lg">Your AI-powered daily fantasy sports assistant</p>
        </header>

        <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.isUser ? "justify-end" : "justify-start"}`}>
              <Card
                className={`max-w-[80%] p-4 ${message.isUser
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/25 border-primary/20"
                    : "bg-card text-card-foreground shadow-lg shadow-accent/10 border-accent/20"
                  } transition-all duration-300 hover:shadow-xl ${message.isUser ? "hover:shadow-primary/35" : "hover:shadow-accent/20"
                  }`}
              >
                <p className="text-sm leading-relaxed">{message.content}</p>
                <span className="text-xs opacity-70 mt-2 block">{message.timestamp.toLocaleTimeString()}</span>
              </Card>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <Card className="bg-card text-card-foreground shadow-lg shadow-accent/10 border-accent/20 p-4">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-accent rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-accent rounded-full animate-bounce delay-100"></div>
                    <div className="w-2 h-2 bg-accent rounded-full animate-bounce delay-200"></div>
                  </div>
                  <span className="text-sm text-muted-foreground">Analyzing...</span>
                </div>
              </Card>
            </div>
          )}
        </div>

        <div className="p-6 border-t border-border/50 backdrop-blur-sm">
          <div className="flex gap-3">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask me about daily fantasy sports strategies, player analysis, or lineup optimization..."
              className="flex-1 bg-input border-border focus:border-primary focus:ring-2 focus:ring-ring shadow-lg transition-all duration-300 focus:shadow-xl focus:shadow-primary/20"
              disabled={isLoading}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/35 transition-all duration-300 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Press Enter to send • Powered by AI for optimal DFS insights
          </p>
        </div>
      </div>
    </div>
  )
}
