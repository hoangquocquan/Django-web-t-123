import { useEffect, useState, type FormEvent } from "react"

import { CanonicalClientError } from "../api/canonical.ts"
import { useAdminTableQuery } from "../hooks/useAdminTableQuery.ts"
import type { AdminApi } from "../services/adminApi.ts"
import type {
  AdminCollection,
  AdminFilterKey,
  AdminOrdering,
  AdminResource,
  AdminResourceResultMap,
} from "../types/admin.ts"
import {
  ADMIN_TABLE_CONFIGS,
  adminTableErrorMessage,
  adminTableStateText,
  type AdminTableState,
} from "./adminTableView.ts"

type TableState = AdminTableState

function rows(
  resource: AdminResource,
  values: AdminResourceResultMap[AdminResource][],
): string[][] {
  switch (resource) {
    case "products":
      return (values as AdminResourceResultMap["products"][]).map((v) => [
        v.sku,
        v.name,
        v.categoryName,
        v.price,
        v.status,
      ])
    case "customers":
      return (values as AdminResourceResultMap["customers"][]).map((v) => [
        v.companyName,
        v.contactName,
        v.country,
        v.status,
      ])
    case "inventory":
      return (values as AdminResourceResultMap["inventory"][]).map((v) => [
        v.productName,
        v.warehouseName,
        v.quantity,
        v.reservedQuantity,
        v.reorderPoint,
      ])
    case "orders":
      return (values as AdminResourceResultMap["orders"][]).map((v) => [
        v.orderNumber,
        v.customerName,
        v.projectName,
        v.totalAmount,
        v.status,
      ])
    case "workflows":
      return (values as AdminResourceResultMap["workflows"][]).map((v) => [
        String(v.orderId),
        v.requestedStatus,
        v.decision,
        v.requestedBy,
        v.reviewedBy,
      ])
    case "transactions":
      return (values as AdminResourceResultMap["transactions"][]).map((v) => [
        v.entityType,
        v.entityId,
        v.action,
        v.actor,
        v.createdAt ?? "",
      ])
  }
}

export function AdminTableStateView({
  resource,
  state,
}: {
  resource: AdminResource
  state: TableState
}) {
  if (state.status === "loading")
    return <p aria-live="polite">{adminTableStateText(state)}</p>
  if (state.status === "empty") return <p>{adminTableStateText(state)}</p>
  if (state.status === "error")
    return (
      <p role="alert" data-error-kind={state.kind}>
        {state.message}
      </p>
    )
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            {ADMIN_TABLE_CONFIGS[resource].headers.map((header) => (
              <th
                className="border-b border-white/20 p-3 text-left"
                key={header}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows(resource, state.page.results).map((row, index) => (
            <tr key={`${state.page.offset}-${index}`}>
              {row.map((cell, cellIndex) => (
                <td className="border-b border-white/10 p-3" key={cellIndex}>
                  {cell || "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function AdminTablePage({
  resource,
  api,
}: {
  resource: AdminResource
  api: AdminApi
}) {
  const controller = useAdminTableQuery(resource)
  const [state, setState] = useState<TableState>({ status: "loading" })
  const config = ADMIN_TABLE_CONFIGS[resource]
  useEffect(() => {
    const abort = new AbortController()
    setState({ status: "loading" })
    void api
      .list(resource, controller.query, abort.signal)
      .then((page) =>
        setState(
          page.results.length ? { status: "ready", page } : { status: "empty" },
        ),
      )
      .catch((error: unknown) => {
        if (error instanceof CanonicalClientError && error.kind === "cancelled")
          return
        const clientError =
          error instanceof CanonicalClientError
            ? error
            : new CanonicalClientError({
                kind: "protocol",
                code: "unexpected_error",
                message: "Unexpected response.",
              })
        setState({
          status: "error",
          kind: clientError.kind,
          message: adminTableErrorMessage(clientError.kind),
        })
      })
    return () => abort.abort()
  }, [api, resource, controller.query])
  const submit = (event: FormEvent) => {
    event.preventDefault()
    controller.applySearch()
  }
  const page = state.status === "ready" ? state.page : null
  return (
    <div className="space-y-4">
      <form className="flex flex-wrap gap-2" onSubmit={submit}>
        <input
          aria-label="Tìm kiếm"
          className="min-w-64 flex-1 border border-white/20 bg-zinc-950 p-2"
          onChange={(event) =>
            controller.setSearchInput(event.currentTarget.value)
          }
          placeholder={config.search}
          value={controller.searchInput}
        />
        <button className="bg-orange-600 px-4 py-2" type="submit">
          Tìm
        </button>
        <button
          className="border border-white/20 px-4 py-2"
          onClick={controller.reset}
          type="button"
        >
          Đặt lại
        </button>
      </form>
      <div className="grid gap-2 md:grid-cols-3">
        {config.filters.map((filter) =>
          filter.options ? (
            <select
              aria-label={filter.label}
              className="border border-white/20 bg-zinc-950 p-2"
              key={filter.key}
              onChange={(event) =>
                controller.setFilter(
                  filter.key as AdminFilterKey<AdminResource>,
                  event.currentTarget.value,
                )
              }
              value={
                (controller.query.filters as Record<string, string>)[
                  filter.key
                ] ?? ""
              }
            >
              <option value="">{filter.label}: Tất cả</option>
              {filter.options.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          ) : (
            <input
              aria-label={filter.label}
              className="border border-white/20 bg-zinc-950 p-2"
              key={filter.key}
              onBlur={(event) =>
                controller.setFilter(
                  filter.key as AdminFilterKey<AdminResource>,
                  event.currentTarget.value,
                )
              }
              placeholder={filter.label}
            />
          ),
        )}
        <select
          aria-label="Sắp xếp"
          className="border border-white/20 bg-zinc-950 p-2"
          onChange={(event) =>
            controller.setOrdering(
              event.currentTarget.value as AdminOrdering<AdminResource> | "",
            )
          }
          value={controller.query.ordering}
        >
          <option value="">Sắp xếp mặc định</option>
          {config.ordering.flatMap(([value, label]) => [
            <option key={value} value={value}>
              {label} ↑
            </option>,
            <option key={`-${value}`} value={`-${value}`}>
              {label} ↓
            </option>,
          ])}
        </select>
      </div>
      <AdminTableStateView resource={resource} state={state} />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label>
          Số dòng{" "}
          <select
            aria-label="Số dòng mỗi trang"
            className="ml-2 bg-zinc-950"
            onChange={(event) =>
              controller.setPageSize(Number(event.currentTarget.value))
            }
            value={controller.query.pageSize}
          >
            {[20, 50, 100].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>
        <span>
          {page
            ? `${page.offset + 1}–${Math.min(page.offset + page.results.length, page.count)} / ${page.count}`
            : ""}
        </span>
        <div className="flex gap-2">
          <button
            className="border border-white/20 px-3 py-1 disabled:opacity-40"
            disabled={controller.query.page <= 1 || state.status === "loading"}
            onClick={() => controller.setPage(controller.query.page - 1)}
          >
            Trước
          </button>
          <button
            className="border border-white/20 px-3 py-1 disabled:opacity-40"
            disabled={!page?.nextOffset || state.status === "loading"}
            onClick={() => controller.setPage(controller.query.page + 1)}
          >
            Sau
          </button>
        </div>
      </div>
    </div>
  )
}
