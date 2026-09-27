import type {
  AdminCollection,
  AdminResource,
  AdminResourceResultMap,
} from "../types/admin.ts"

type LoadingState = { status: "loading" }
type EmptyState = { status: "empty" }
type ReadyState = {
  status: "ready"
  page: AdminCollection<AdminResourceResultMap[AdminResource]>
}
type ErrorState = {
  status: "error"
  kind: string
  message: string
}
export type AdminTableState = LoadingState | EmptyState | ReadyState | ErrorState

type FilterConfig = {
  key: string
  label: string
  options?: ReadonlyArray<readonly [string, string]>
}
type Config = {
  search: string
  filters: readonly FilterConfig[]
  ordering: ReadonlyArray<readonly [string, string]>
  headers: readonly string[]
}

export const ADMIN_TABLE_CONFIGS: Record<AdminResource, Config> = {
  products: {
    search: "Tìm mã, tên hoặc vật liệu",
    filters: [
      {
        key: "status",
        label: "Trạng thái",
        options: [
          ["draft", "Draft"],
          ["published", "Published"],
          ["archived", "Archived"],
        ],
      },
      {
        key: "active",
        label: "Hoạt động",
        options: [
          ["true", "Active"],
          ["false", "Inactive"],
        ],
      },
      { key: "material", label: "Vật liệu" },
    ],
    ordering: [
      ["created_at", "Ngày tạo"],
      ["product_code", "Mã sản phẩm"],
      ["name", "Tên"],
    ],
    headers: ["SKU", "Tên", "Danh mục", "Giá", "Trạng thái"],
  },
  customers: {
    search: "Tìm công ty hoặc người liên hệ",
    filters: [
      {
        key: "status",
        label: "Trạng thái",
        options: [
          ["active", "Active"],
          ["inactive", "Inactive"],
          ["lead", "Lead"],
        ],
      },
    ],
    ordering: [
      ["created_at", "Ngày tạo"],
      ["company_name", "Công ty"],
      ["contact_name", "Liên hệ"],
    ],
    headers: ["Công ty", "Liên hệ", "Quốc gia", "Trạng thái"],
  },
  inventory: {
    search: "Tìm sản phẩm hoặc vật liệu",
    filters: [
      { key: "warehouse", label: "Kho" },
      {
        key: "availability",
        label: "Khả dụng",
        options: [
          ["positive", "Lớn hơn 0"],
          ["zero", "Bằng 0"],
        ],
      },
    ],
    ordering: [
      ["quantity", "Số lượng"],
      ["updated_at", "Cập nhật"],
    ],
    headers: ["Sản phẩm", "Kho", "Số lượng", "Đã giữ", "Điểm đặt lại"],
  },
  orders: {
    search: "Tìm đơn hàng hoặc khách hàng",
    filters: [
      {
        key: "workflow_status",
        label: "Workflow",
        options: [
          ["CONFIRMED", "Confirmed"],
          ["IN_PROGRESS", "In progress"],
          ["ON_HOLD", "On hold"],
          ["COMPLETED", "Completed"],
          ["CANCELLED", "Cancelled"],
        ],
      },
      {
        key: "status",
        label: "Trạng thái",
        options: [
          ["new", "New"],
          ["approved", "Approved"],
          ["processing", "Processing"],
          ["completed", "Completed"],
          ["cancelled", "Cancelled"],
        ],
      },
    ],
    ordering: [
      ["order_date", "Ngày đặt hàng"],
      ["expected_delivery_date", "Ngày giao dự kiến"],
    ],
    headers: ["Đơn hàng", "Khách hàng", "Dự án", "Giá trị", "Trạng thái"],
  },
  workflows: {
    search: "Tìm đơn hàng hoặc người xử lý",
    filters: [
      {
        key: "decision",
        label: "Quyết định",
        options: [
          ["pending", "Pending"],
          ["approved", "Approved"],
          ["rejected", "Rejected"],
        ],
      },
      {
        key: "requested_status",
        label: "Trạng thái yêu cầu",
        options: [
          ["new", "New"],
          ["approved", "Approved"],
          ["processing", "Processing"],
          ["completed", "Completed"],
          ["cancelled", "Cancelled"],
        ],
      },
    ],
    ordering: [
      ["created_at", "Ngày tạo"],
      ["order", "Đơn hàng"],
    ],
    headers: [
      "Order ID",
      "Trạng thái yêu cầu",
      "Quyết định",
      "Người yêu cầu",
      "Người duyệt",
    ],
  },
  transactions: {
    search: "Tìm entity, action hoặc actor",
    filters: [
      { key: "entity_type", label: "Entity type" },
      { key: "action", label: "Action" },
    ],
    ordering: [["created_at", "Ngày tạo"]],
    headers: ["Entity", "Entity ID", "Action", "Actor", "Ngày tạo"],
  },
}

export function adminTableStateText(state: AdminTableState): string {
  if (state.status === "loading") return "Đang tải dữ liệu…"
  if (state.status === "empty") return "Không có dữ liệu phù hợp."
  if (state.status === "error") return state.message
  return `${state.page.offset + 1}–${Math.min(state.page.offset + state.page.results.length, state.page.count)} / ${state.page.count}`
}

export function adminTableErrorMessage(kind: string): string {
  if (kind === "validation")
    return "Truy vấn không hợp lệ. Hãy kiểm tra bộ lọc."
  if (kind === "authentication")
    return "Phiên đăng nhập đã hết hạn hoặc không hợp lệ."
  if (kind === "permission") return "Bạn không có quyền xem dữ liệu này."
  if (kind === "timeout") return "Yêu cầu đã hết thời gian chờ."
  if (kind === "cancelled") return "Yêu cầu đã bị hủy."
  if (kind === "network") return "Không thể kết nối máy chủ."
  return "Không thể tải dữ liệu quản trị."
}
