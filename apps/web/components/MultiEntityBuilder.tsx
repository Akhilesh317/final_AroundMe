'use client'

import { useState } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { PlusIcon, XIcon } from 'lucide-react'

interface MultiEntityBuilderProps {
  value: any
  onChange: (value: any) => void
}

export function MultiEntityBuilder({ value, onChange }: MultiEntityBuilderProps) {
  const [entities, setEntities] = useState<any[]>(value?.entities || [])
  const [relations, setRelations] = useState<any[]>(value?.relations || [])

  const addEntity = () => {
    const newEntity = {
      kind: '',
      must_haves: [],
      filters: {},
    }
    const updated = [...entities, newEntity]
    setEntities(updated)
    updateValue(updated, relations)
  }

  const removeEntity = (index: number) => {
    const updated = entities.filter((_, i) => i !== index)
    // Remove relations that reference this entity
    const updatedRelations = relations.filter(
      (r) => r.left !== index && r.right !== index
    )
    setEntities(updated)
    setRelations(updatedRelations)
    updateValue(updated, updatedRelations)
  }

  const updateEntity = (index: number, field: string, value: any) => {
    const updated = entities.map((e, i) =>
      i === index ? { ...e, [field]: value } : e
    )
    setEntities(updated)
    updateValue(updated, relations)
  }

  const addMustHave = (entityIndex: number, mustHave: string) => {
    if (!mustHave.trim()) return
    const updated = entities.map((e, i) =>
      i === entityIndex
        ? { ...e, must_haves: [...(e.must_haves || []), mustHave.trim()] }
        : e
    )
    setEntities(updated)
    updateValue(updated, relations)
  }

  const removeMustHave = (entityIndex: number, mustHaveIndex: number) => {
    const updated = entities.map((e, i) =>
      i === entityIndex
        ? { ...e, must_haves: e.must_haves.filter((_: any, j: number) => j !== mustHaveIndex) }
        : e
    )
    setEntities(updated)
    updateValue(updated, relations)
  }

  const addRelation = () => {
    if (entities.length < 2) return
    const newRelation = {
      left: 0,
      right: 1,
      relation: 'NEAR',
      distance_m: 500,
    }
    const updated = [...relations, newRelation]
    setRelations(updated)
    updateValue(entities, updated)
  }

  const removeRelation = (index: number) => {
    const updated = relations.filter((_, i) => i !== index)
    setRelations(updated)
    updateValue(entities, updated)
  }

  const updateRelation = (index: number, field: string, value: any) => {
    const updated = relations.map((r, i) =>
      i === index ? { ...r, [field]: value } : r
    )
    setRelations(updated)
    updateValue(entities, updated)
  }

  const updateValue = (ents: any[], rels: any[]) => {
    onChange({
      entities: ents,
      relations: rels,
      radius_m: 3000,
      top_k: 30,
    })
  }

  return (
    <div className="space-y-4">
      {/* Entities */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium">Entities</h4>
          <Button size="sm" variant="outline" onClick={addEntity}>
            <PlusIcon className="h-4 w-4 mr-1" />
            Add Entity
          </Button>
        </div>

        <div className="space-y-3">
          {entities.map((entity, index) => (
            <Card key={index}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">Entity {index + 1}</CardTitle>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => removeEntity(index)}
                  >
                    <XIcon className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-xs font-medium mb-1 block">Type</label>
                  <Input
                    placeholder="e.g., restaurant, park, cafe"
                    value={entity.kind}
                    onChange={(e) =>
                      updateEntity(index, 'kind', e.target.value)
                    }
                    size={1}
                  />
                </div>

                <div>
                  <label className="text-xs font-medium mb-1 block">
                    Must-Haves
                  </label>
                  <div className="flex gap-2 mb-2">
                    <Input
                      placeholder="e.g., playground, wifi"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          addMustHave(index, e.currentTarget.value)
                          e.currentTarget.value = ''
                        }
                      }}
                      size={1}
                    />
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {entity.must_haves?.map((mh: string, mhIndex: number) => (
                      <Badge key={mhIndex} variant="secondary">
                        {mh}
                        <button
                          onClick={() => removeMustHave(index, mhIndex)}
                          className="ml-1 hover:text-destructive"
                        >
                          <XIcon className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Relations */}
      {entities.length >= 2 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium">Relations</h4>
            <Button size="sm" variant="outline" onClick={addRelation}>
              <PlusIcon className="h-4 w-4 mr-1" />
              Add Relation
            </Button>
          </div>

          <div className="space-y-2">
            {relations.map((relation, index) => (
              <Card key={index}>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2">
                    <select
                      className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                      value={relation.left}
                      onChange={(e) =>
                        updateRelation(index, 'left', parseInt(e.target.value))
                      }
                    >
                      {entities.map((_, i) => (
                        <option key={i} value={i}>
                          Entity {i + 1}
                        </option>
                      ))}
                    </select>

                    <select
                      className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                      value={relation.relation}
                      onChange={(e) =>
                        updateRelation(index, 'relation', e.target.value)
                      }
                    >
                      <option value="NEAR">NEAR</option>
                      <option value="WITHIN_DISTANCE">WITHIN</option>
                    </select>

                    <select
                      className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                      value={relation.right}
                      onChange={(e) =>
                        updateRelation(index, 'right', parseInt(e.target.value))
                      }
                    >
                      {entities.map((_, i) => (
                        <option key={i} value={i}>
                          Entity {i + 1}
                        </option>
                      ))}
                    </select>

                    {relation.relation === 'WITHIN_DISTANCE' && (
                      <Input
                        type="number"
                        placeholder="meters"
                        value={relation.distance_m}
                        onChange={(e) =>
                          updateRelation(
                            index,
                            'distance_m',
                            parseInt(e.target.value)
                          )
                        }
                        className="w-24"
                      />
                    )}

                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeRelation(index)}
                    >
                      <XIcon className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}