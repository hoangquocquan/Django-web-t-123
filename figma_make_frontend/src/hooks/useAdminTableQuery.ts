import { useEffect, useReducer, useState } from "react"
import type {
  AdminFilterKey,
  AdminOrdering,
  AdminResource,
  AdminTableQuery,
} from "../types/admin.ts"

export const DEFAULT_ADMIN_PAGE_SIZE = 20
export const MAX_ADMIN_PAGE_SIZE = 100
export const ADMIN_QUERY_CONTRACTS = {
  products: {
    filters: ["status", "active", "material"],
    ordering: ["created_at", "product_code", "name"],
  },
  customers: {
    filters: ["status"],
    ordering: ["created_at", "company_name", "contact_name"],
  },
  inventory: {
    filters: ["warehouse", "availability"],
    ordering: ["quantity", "updated_at"],
  },
  orders: {
    filters: ["workflow_status", "status"],
    ordering: ["order_date", "expected_delivery_date"],
  },
  workflows: {
    filters: ["decision", "requested_status"],
    ordering: ["created_at", "order"],
  },
  transactions: {
    filters: ["entity_type", "action"],
    ordering: ["created_at"],
  },
} as const satisfies Record<AdminResource, {
  filters: readonly string[]
  ordering: readonly string[]
}>
type PageAction = {
  type: "page"
  page: number
}
type PageSizeAction = {
  type: "pageSize"
  pageSize: number
}
type SearchAction = {
  type: "search"
  search: string
}
type FilterAction<R extends AdminResource,> = {
  type: "filter"
  name: AdminFilterKey<R>
  value: string
}
type OrderingAction<R extends AdminResource,> = {
  type: "ordering"
  ordering: AdminOrdering<R> | ""
}
type ResetAction = { type: "reset" }
export type AdminTableQueryAction<R extends AdminResource,> = PageAction | PageSizeAction | SearchAction | FilterAction<R> | OrderingAction<R> | ResetAction
export function clampAdminPageSize(value: number): number {
  if (!Number.isFinite(value)) return DEFAULT_ADMIN_PAGE_SIZE
  return Math.min(MAX_ADMIN_PAGE_SIZE, Math.max(1, Math.trunc(value)))
}
export function initialAdminTableQuery<R extends AdminResource,>(): AdminTableQuery<R> {
  return {
    page: 1,
    pageSize: DEFAULT_ADMIN_PAGE_SIZE,
    search: "",
    filters: {},
    ordering: "",
  }
}
export function reduceAdminTableQuery<R extends AdminResource>(
  resource: R,
  state: AdminTableQuery<R>,
  action: AdminTableQueryAction<R>,
): AdminTableQuery<R> {
  switch (action.type) {
    case "page":
      return { ...state, page: Math.max(1, Math.trunc(action.page) || 1) }
    case "pageSize":
      return {
        ...state,
        page: 1,
        pageSize: clampAdminPageSize(action.pageSize),
      }
    case "search":
      return { ...state, page: 1, search: action.search.trim() }
    case "filter": {
      if (
        !(ADMIN_QUERY_CONTRACTS[resource]
          .filters as readonly string[]).includes(action.name)
      )
        return state
      const filters = { ...state.filters }
      if (action.value.trim()) filters[action.name] = action.value.trim()
      else delete filters[action.name]
      return { ...state, page: 1, filters }
    }
    case "ordering": {
      const field = action.ordering.startsWith("-")
        ? action.ordering.slice(1)
        : action.ordering
      if (
        field &&
        !(ADMIN_QUERY_CONTRACTS[resource]
          .ordering as readonly string[]).includes(field)
      )
        return state
      return { ...state, page: 1, ordering: action.ordering }
    }
    case "reset":
      return initialAdminTableQuery<R>()
  }
}
export function useAdminTableQuery<R extends AdminResource>(resource: R) {
  const [query, dispatch] = useReducer(
    (state: AdminTableQuery<R>, action: AdminTableQueryAction<R>) =>
      reduceAdminTableQuery(resource, state, action),
    undefined,
    initialAdminTableQuery<R>,
  )
  const [searchInput, setSearchInput] = useState("")
  useEffect(() => {
    setSearchInput("")
    dispatch({ type: "reset" })
  }, [resource])
  return {
    query,
    searchInput,
    setSearchInput,
    applySearch: () => dispatch({ type: "search", search: searchInput }),
    setPage: (page: number) => dispatch({ type: "page", page }),
    setPageSize: (pageSize: number) => dispatch({ type: "pageSize", pageSize }),
    setFilter: (name: AdminFilterKey<R>, value: string) =>
      dispatch({ type: "filter", name, value }),
    setOrdering: (ordering: AdminOrdering<R> | "") =>
      dispatch({ type: "ordering", ordering }),
    reset: () => {
      setSearchInput("")
      dispatch({ type: "reset" })
    },
  }
}
