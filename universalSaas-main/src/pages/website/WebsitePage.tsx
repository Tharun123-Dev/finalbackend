import { Globe, Layout, Palette, Search, Image, Eye } from 'lucide-react'
import { PageHeader } from '@/components/shared/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'

const templates = [
  { name: 'Corporate Pro', category: 'Business' },
  { name: 'SaaS Landing', category: 'Tech' },
  { name: 'Temple Trust', category: 'Non-profit' },
  { name: 'Law Firm', category: 'Professional' },
]

export function WebsitePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="My Website"
        description="Build and customize your organization website."
        actions={
          <Button className="gap-2">
            <Eye className="h-4 w-4" />
            Live Preview
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Layout className="h-4 w-4" />
                Template Gallery
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2">
                {templates.map((t) => (
                  <div
                    key={t.name}
                    className="group cursor-pointer overflow-hidden rounded-xl border border-border transition-shadow hover:shadow-md"
                  >
                    <div className="aspect-video bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800" />
                    <div className="p-3">
                      <p className="font-medium">{t.name}</p>
                      <Badge variant="secondary" className="mt-1">{t.category}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base">Page Builder</CardTitle></CardHeader>
            <CardContent>
              <div className="grid min-h-[200px] gap-2 rounded-lg border-2 border-dashed border-border p-4">
                {['Header', 'Hero Banner', 'Content Block', 'Footer'].map((block) => (
                  <div
                    key={block}
                    className="flex items-center justify-center rounded-lg border border-dashed border-muted-foreground/30 bg-muted/30 py-6 text-sm text-muted-foreground"
                  >
                    Drag {block} here
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardContent className="p-4">
              <Tabs defaultValue="theme">
                <TabsList className="w-full">
                  <TabsTrigger value="theme" className="flex-1">Theme</TabsTrigger>
                  <TabsTrigger value="seo" className="flex-1">SEO</TabsTrigger>
                  <TabsTrigger value="domain" className="flex-1">Domain</TabsTrigger>
                </TabsList>
                <TabsContent value="theme" className="space-y-3 pt-4">
                  <div className="flex items-center gap-2">
                    <Palette className="h-4 w-4" />
                    <span className="text-sm font-medium">Color Theme</span>
                  </div>
                  <div className="flex gap-2">
                    {['#6366f1', '#10b981', '#f59e0b', '#ef4444'].map((c) => (
                      <button
                        key={c}
                        type="button"
                        className="h-8 w-8 rounded-full ring-2 ring-offset-2 ring-transparent hover:ring-primary"
                        style={{ backgroundColor: c }}
                      />
                    ))}
                  </div>
                </TabsContent>
                <TabsContent value="seo" className="space-y-3 pt-4">
                  <Input placeholder="Meta title" />
                  <Input placeholder="Meta description" />
                  <Button variant="outline" size="sm" className="w-full gap-2">
                    <Search className="h-4 w-4" />
                    SEO Analysis
                  </Button>
                </TabsContent>
                <TabsContent value="domain" className="space-y-3 pt-4">
                  <Input placeholder="yourcompany.com" />
                  <Badge variant="success">SSL Active</Badge>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <Image className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Banner Management</p>
                <p className="text-xs text-muted-foreground">3 active banners</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-muted/30">
            <CardContent className="flex aspect-video items-center justify-center p-4">
              <Globe className="h-12 w-12 text-muted-foreground/50" />
              <span className="sr-only">Preview</span>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}


