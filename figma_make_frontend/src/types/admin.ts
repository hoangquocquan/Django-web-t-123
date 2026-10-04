export const ADMIN_RESOURCES = [
  "products",
  "customers",
  "inventory",
  "orders",
  "workflows",
  "transactions",
] as const
export type AdminResource = typeof ADMIN_RESOURCES[number]
export type AdminFilterKeyMap = {
  products: "status" | "active" | "material"
  customers: "status"
  inventory: "warehouse" | "availability"
  orders: "workflow_status" | "status"
  workflows: "decision" | "requested_status"
  transactions: "entity_type" | "action"
}
export type AdminOrderingMap = {
  products: "created_at" | "product_code" | "name"
  customers: "created_at" | "company_name" | "contact_name"
  inventory: "quantity" | "updated_at"
  orders: "order_date" | "expected_delivery_date"
  workflows: "created_at" | "order"
  transactions: "created_at"
}
export type AdminFilterKey<R extends AdminResource> = AdminFilterKeyMap[R]
export type AdminOrdering<R extends AdminResource,> = AdminOrderingMap[R] | `-${AdminOrderingMap[R]}`
export type AdminTableQuery<R extends AdminResource = AdminResource,> = {
  page: number
  pageSize: number
  search: string
  filters: Partial<Record<AdminFilterKey<R>, string>>
  ordering: AdminOrdering<R> | ""
}
export type AdminCollection<T,> = {
  count: number
  limit: number
  offset: number
  nextOffset: number | null
  results: T[]
}
export type AdminProduct = {
  id: number
  sku: string
  name: string
  status: string
  price: string
  categoryName: string
}
export type AdminCustomer = {
  id: number
  companyName: string
  contactName: string
  country: string
  status: string
}
export type AdminInventoryItem = {
  id: number
  productName: string
  warehouseName: string
  quantity: string
  reservedQuantity: string
  reorderPoint: string
}
export type AdminOrder = {
  id: number
  orderNumber: string
  customerName: string
  projectName: string
  status: string
  totalAmount: string
}
export type AdminWorkflow = {
  id: number
  orderId: number
  requestedStatus: string
  decision: string
  requestedBy: string
  reviewedBy: string
}
export type AdminTransaction = {
  id: number
  entityType: string
  entityId: string
  action: string
  actor: string
  createdAt: string | null
}
export type AdminResourceResultMap = {
  products: AdminProduct
  customers: AdminCustomer
  inventory: AdminInventoryItem
  orders: AdminOrder
  workflows: AdminWorkflow
  transactions: AdminTransaction
}
