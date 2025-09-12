"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle, Clock, ExternalLink, Server, Database, FileText, AlertCircle, RefreshCw } from "lucide-react"
import { useState, useEffect } from "react"
import { apiClient, type ApiStats } from "@/libs/api"

const getBaseUrl = () => {
  return apiClient['baseUrl'] || (typeof window !== 'undefined' ? window.location.origin : '')
}

export default function ApiStatusPage() {
  const [apiInfo, setApiInfo] = useState<ApiStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async (showRefreshSpinner = false) => {
    try {
      if (showRefreshSpinner) setIsRefreshing(true)
      setError(null)
      const stats = await apiClient.getStats()
      setApiInfo(stats)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
    } finally {
      setIsLoading(false)
      if (showRefreshSpinner) setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchStats()
    // Автоматическое обновление каждые 30 секунд
    const interval = setInterval(() => fetchStats(), 30000)
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = () => {
    fetchStats(true)
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString("ru-RU", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
  }

  const getEndpointIcon = (endpoint: string) => {
    if (endpoint.includes("docs") || endpoint.includes("redoc")) {
      return <FileText className="h-4 w-4" />
    }
    if (endpoint.includes("schedules")) {
      return <Database className="h-4 w-4" />
    }
    return <Server className="h-4 w-4" />
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <div className="text-center space-y-4">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto" />
          <p className="text-muted-foreground">Загрузка данных API...</p>
        </div>
      </div>
    )
  }

  if (!apiInfo) {
    return (
      <div className="min-h-screen bg-background p-6 flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto" />
          <p className="text-muted-foreground">Ошибка загрузки данных API</p>
          <Button onClick={() => fetchStats()} variant="outline">
            Повторить попытку
          </Button>
        </div>
      </div>
    )
  }

  const getStatusIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case 'OK':
        return <CheckCircle className="h-6 w-6 text-green-500" />
      case 'ERROR':
        return <AlertCircle className="h-6 w-6 text-red-500" />
      default:
        return <Clock className="h-6 w-6 text-yellow-500" />
    }
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status.toUpperCase()) {
      case 'OK':
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
      case 'ERROR':
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
      default:
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
    }
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-4">
            <h1 className="text-4xl font-bold text-foreground">API Dashboard</h1>
            <Button 
              onClick={handleRefresh} 
              variant="outline" 
              size="sm" 
              disabled={isRefreshing}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Обновление...' : 'Обновить'}
            </Button>
          </div>
          <p className="text-muted-foreground text-lg">Мониторинг состояния API</p>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
                <AlertCircle className="h-4 w-4" />
                <span className="font-medium">Предупреждение:</span>
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Status Overview */}
        <Card className="border-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(apiInfo.status)}
                Статус сервиса
              </CardTitle>
              <Badge variant="secondary" className={getStatusBadgeClass(apiInfo.status)}>
                {apiInfo.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h3 className="font-semibold text-foreground">Информация о сервисе</h3>
                <div className="space-y-1 text-sm">
                  <p>
                    <span className="font-medium">Название:</span> {apiInfo.service}
                  </p>
                  <p>
                    <span className="font-medium">Версия:</span> {apiInfo.version}
                  </p>
                  {apiInfo.git && (
                    <>
                      {apiInfo.git.branch && (
                        <p>
                          <span className="font-medium">Ветка:</span> <code className="bg-muted px-1 rounded text-xs">{apiInfo.git.branch}</code>
                        </p>
                      )}
                      {apiInfo.git.commit && (
                        <p>
                          <span className="font-medium">Коммит:</span> <code className="bg-muted px-1 rounded text-xs">{apiInfo.git.commit}</code>
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>
              <div className="space-y-2">
                <h3 className="font-semibold text-foreground flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Последнее обновление
                </h3>
                <p className="text-sm text-muted-foreground">{formatTimestamp(apiInfo.timestamp)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Endpoints */}
        <Card>
          <CardHeader>
            <CardTitle>Доступные эндпоинты</CardTitle>
            <CardDescription>Список всех доступных API эндпоинтов и их назначение</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              {Object.entries(apiInfo.endpoints).map(([key, path]) => (
                <div
                  key={key}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {getEndpointIcon(path)}
                    <div>
                      <h4 className="font-medium capitalize">{key}</h4>
                      <p className="text-sm text-muted-foreground font-mono">{path}</p>
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="gap-2 bg-transparent"
                    onClick={() => window.open(`${apiClient['baseUrl']}${path}`, '_blank')}
                  >
                    <ExternalLink className="h-3 w-3" />
                    Открыть
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Additional Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Документация</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Swagger UI</span>
                <Button variant="outline" size="sm" onClick={() => window.open(`${apiClient['baseUrl']}/docs`, '_blank')}>
                  /docs
                </Button>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">ReDoc</span>
                <Button variant="outline" size="sm" onClick={() => window.open(`${apiClient['baseUrl']}/redoc`, '_blank')}>
                  /redoc
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Основные функции</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Получение расписания групп
              </div>
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Получение кода недели
              </div>
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="h-4 w-4 text-green-500" />
                REST API архитектура
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
