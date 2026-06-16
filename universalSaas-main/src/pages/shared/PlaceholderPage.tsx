import { motion } from 'framer-motion'
import { PageHeader } from '@/components/shared/PageHeader'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'

interface PlaceholderPageProps {
  title: string
  description: string
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        description={description}
        actions={
          <Button>
            <Plus className="h-4 w-4" />
            Create New
          </Button>
        }
      />
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <Card className="border-dashed">
          <CardContent className="flex min-h-[320px] flex-col items-center justify-center p-12 text-center">
            <p className="text-lg font-medium text-muted-foreground">
              {title} module — dynamic content loads here
            </p>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              This module is configured via the universal platform registry and will render
              widgets based on tenant permissions.
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}


