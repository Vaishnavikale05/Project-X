import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import { ApiError } from "../../api/client";
import { useAuth } from "../auth/useAuth";
import { errorMessage, infrastructureApi } from "./api";
import type { Camera, CameraInput, Classroom, ClassroomInput, Institution } from "./types";

function useReload() {
  const [version, setVersion] = useState(0);
  return [version, () => setVersion((value) => value + 1)] as const;
}

function PageTitle({ title, description }: { title: string; description?: string }) {
  return (
    <header className="page-heading">
      <p className="eyebrow">Infrastructure</p>
      <h1>{title}</h1>
      {description && <p>{description}</p>}
    </header>
  );
}

function Notice({ children, kind = "error" }: { children: string; kind?: "error" | "success" }) {
  return (
    <p className={`notice notice-${kind}`} role={kind === "error" ? "alert" : "status"}>
      {children}
    </p>
  );
}

function requestError(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    return "Your session expired. Sign in again to continue.";
  }
  if (error instanceof ApiError && error.status === 403) {
    return "You do not have permission to make this change.";
  }
  if (error instanceof ApiError && error.status === 404) {
    return "This infrastructure record is no longer available in your institution.";
  }
  return errorMessage(error);
}

function FieldError({ error }: { error: unknown }) {
  if (!(error instanceof ApiError) || error.status !== 400 || !error.details) return null;
  const details = error.details as Record<string, unknown>;
  const messages = Object.entries(details).flatMap(([field, value]) => {
    const list = Array.isArray(value) ? value : [value];
    return list
      .filter((item): item is string => typeof item === "string")
      .map((item) => `${field}: ${item}`);
  });
  return messages.length ? <Notice>{messages.join(" ")}</Notice> : null;
}

function ClassroomForm({
  initial,
  onSubmit,
  submitLabel,
}: {
  initial?: Classroom;
  onSubmit: (input: ClassroomInput) => Promise<void>;
  submitLabel: string;
}) {
  const [code, setCode] = useState(initial?.code ?? "");
  const [name, setName] = useState(initial?.name ?? "");
  const [capacity, setCapacity] = useState(initial?.capacity?.toString() ?? "");
  const [active, setActive] = useState(initial?.is_active ?? true);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSubmit({
        code: code.trim(),
        name: name.trim(),
        capacity: capacity.trim() ? Number(capacity) : null,
        ...(initial ? { is_active: active } : {}),
      });
    } catch (cause) {
      setError(cause);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="resource-form" onSubmit={(event) => void submit(event)}>
      {error !== null && <Notice>{requestError(error)}</Notice>}
      <FieldError error={error} />
      <label>
        Room code
        <input
          autoComplete="off"
          maxLength={40}
          onChange={(event) => setCode(event.target.value)}
          required
          value={code}
        />
      </label>
      <label>
        Display name <span className="muted">(optional)</span>
        <input maxLength={120} onChange={(event) => setName(event.target.value)} value={name} />
      </label>
      <label>
        Capacity <span className="muted">(optional)</span>
        <input
          inputMode="numeric"
          max={32767}
          min={1}
          onChange={(event) => setCapacity(event.target.value)}
          type="number"
          value={capacity}
        />
      </label>
      {initial && (
        <label className="check-field">
          <input
            checked={active}
            onChange={(event) => setActive(event.target.checked)}
            type="checkbox"
          />
          Active
        </label>
      )}
      <button disabled={busy} type="submit">
        {busy ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}

function CameraForm({
  classrooms,
  initial,
  initialClassroomId,
  onSubmit,
  submitLabel,
}: {
  classrooms: Classroom[];
  initial?: Camera;
  initialClassroomId?: string;
  onSubmit: (input: CameraInput) => Promise<void>;
  submitLabel: string;
}) {
  const [code, setCode] = useState(initial?.code ?? "");
  const [displayName, setDisplayName] = useState(initial?.display_name ?? "");
  const [classroomId, setClassroomId] = useState(initial?.classroom_id ?? initialClassroomId ?? "");
  const [status, setStatus] = useState<Camera["status"]>(initial?.status ?? "ACTIVE");
  const [resolution, setResolution] = useState(initial?.resolution ?? "");
  const [frameRate, setFrameRate] = useState(initial?.frame_rate?.toString() ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSubmit({
        code: code.trim(),
        display_name: displayName.trim(),
        ...(!initial ? { classroom_id: classroomId } : {}),
        source_type: "LOCAL_FILE",
        status,
        resolution: resolution.trim() || null,
        frame_rate: frameRate.trim() ? Number(frameRate) : null,
        description: description.trim(),
      });
    } catch (cause) {
      setError(cause);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="resource-form" onSubmit={(event) => void submit(event)}>
      {error !== null && <Notice>{requestError(error)}</Notice>}
      <FieldError error={error} />
      <label>
        Camera code
        <input
          autoComplete="off"
          maxLength={80}
          onChange={(event) => setCode(event.target.value)}
          required
          value={code}
        />
      </label>
      <label>
        Display name
        <input
          maxLength={120}
          onChange={(event) => setDisplayName(event.target.value)}
          required
          value={displayName}
        />
      </label>
      {!initial && (
        <label>
          Classroom
          <select
            onChange={(event) => setClassroomId(event.target.value)}
            required
            value={classroomId}
          >
            <option value="">Choose a classroom</option>
            {classrooms
              .filter((room) => room.is_active)
              .map((room) => (
                <option key={room.id} value={room.id}>
                  {room.code}
                  {room.name ? ` — ${room.name}` : ""}
                </option>
              ))}
          </select>
        </label>
      )}
      <label>
        Source type
        <input readOnly value="LOCAL_FILE" />
      </label>
      <p className="muted">
        This records camera metadata only. College CCTV/NVR/VMS connectivity is not configured.
      </p>
      <label>
        Resolution <span className="muted">(optional, e.g. 1920x1080)</span>
        <input
          maxLength={32}
          onChange={(event) => setResolution(event.target.value)}
          value={resolution}
        />
      </label>
      <label>
        Frame rate <span className="muted">(optional)</span>
        <input
          inputMode="decimal"
          min={0.001}
          onChange={(event) => setFrameRate(event.target.value)}
          step="0.001"
          type="number"
          value={frameRate}
        />
      </label>
      <label>
        Description <span className="muted">(optional)</span>
        <textarea
          maxLength={500}
          onChange={(event) => setDescription(event.target.value)}
          value={description}
        />
      </label>
      <label>
        Status
        <select
          onChange={(event) => setStatus(event.target.value as Camera["status"])}
          value={status}
        >
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
        </select>
      </label>
      <button disabled={busy} type="submit">
        {busy ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}

export function AdminDashboardPage() {
  const { accessToken } = useAuth();
  const [reload, refresh] = useReload();
  const [data, setData] = useState<{
    institution: Institution;
    classroomCount: number;
    activeClassrooms: number;
    cameraCount: number;
    activeCameras: number;
  } | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;
    let active = true;
    Promise.all([
      infrastructureApi.institutions(accessToken),
      infrastructureApi.classrooms(accessToken, { page_size: 1 }),
      infrastructureApi.classrooms(accessToken, { is_active: true, page_size: 1 }),
      infrastructureApi.cameras(accessToken),
      infrastructureApi.cameras(accessToken, { status: "ACTIVE" }),
    ])
      .then(([institutions, classrooms, activeRooms, cameras, activeCameras]) => {
        if (!active) return;
        if (!institutions.results[0]) throw new Error("Institution context is not available.");
        setData({
          institution: institutions.results[0],
          classroomCount: classrooms.count,
          activeClassrooms: activeRooms.count,
          cameraCount: cameras.count,
          activeCameras: activeCameras.count,
        });
        setError(null);
      })
      .catch((cause: unknown) => active && setError(cause))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [accessToken, reload]);

  return (
    <section className="content-page">
      <PageTitle
        title="Infrastructure overview"
        description="Current institution, physical classrooms, and registered camera metadata."
      />
      {loading && <p role="status">Loading infrastructure…</p>}
      {error !== null && <Notice>{requestError(error)}</Notice>}
      {!loading && !error && data && (
        <>
          <div className="summary-grid">
            <article className="summary-card">
              <span>Institution</span>
              <strong>{data.institution.name}</strong>
              <small>
                {data.institution.code} · {data.institution.is_active ? "Active" : "Inactive"}
              </small>
              <Link to="/admin/institution">View institution</Link>
            </article>
            <article className="summary-card">
              <span>Classrooms</span>
              <strong>{data.classroomCount}</strong>
              <small>{data.activeClassrooms} active</small>
              <Link to="/admin/classrooms">Manage classrooms</Link>
            </article>
            <article className="summary-card">
              <span>Registered cameras</span>
              <strong>{data.cameraCount}</strong>
              <small>{data.activeCameras} active · connection status is not monitored</small>
              <Link to="/admin/cameras">Manage cameras</Link>
            </article>
          </div>
          <button
            className="secondary-button"
            onClick={() => {
              setLoading(true);
              refresh();
            }}
            type="button"
          >
            Refresh counts
          </button>
        </>
      )}
    </section>
  );
}

export function InstitutionPage() {
  const { accessToken, user } = useAuth();
  const [reload, refresh] = useReload();
  const [institution, setInstitution] = useState<Institution | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken || !user) return;
    let active = true;
    infrastructureApi
      .institution(accessToken, user.institution_id)
      .then((result) => active && setInstitution(result))
      .catch((cause: unknown) => active && setError(cause))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [accessToken, user, reload]);

  async function save(input: { name: string; code: string; timezone: string; is_active: boolean }) {
    if (!accessToken || !institution) return;
    const updated = await infrastructureApi.updateInstitution(accessToken, institution.id, input);
    setInstitution(updated);
    setSuccess("Institution details saved.");
    setError(null);
  }

  return (
    <section className="content-page">
      <PageTitle
        title="Institution context"
        description="This institution is provisioned during deployment. Institution creation is not available to local administrators."
      />
      {loading && <p role="status">Loading institution…</p>}
      {error !== null && <Notice>{requestError(error)}</Notice>}
      {success && <Notice kind="success">{success}</Notice>}
      {!loading && institution && (
        <InstitutionEditForm
          key={`${institution.id}-${reload}`}
          institution={institution}
          onSaved={save}
          onRefresh={() => {
            setLoading(true);
            refresh();
          }}
        />
      )}
    </section>
  );
}

function InstitutionEditForm({
  institution,
  onSaved,
  onRefresh,
}: {
  institution: Institution;
  onSaved: (values: {
    name: string;
    code: string;
    timezone: string;
    is_active: boolean;
  }) => Promise<void>;
  onRefresh: () => void;
}) {
  const [name, setName] = useState(institution.name);
  const [code, setCode] = useState(institution.code);
  const [timezone, setTimezone] = useState(institution.timezone);
  const [active, setActive] = useState(institution.is_active);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSaved({ name, code, timezone, is_active: active });
    } catch (cause) {
      setError(cause);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="resource-form narrow-form" onSubmit={(event) => void submit(event)}>
      {error !== null && <Notice>{requestError(error)}</Notice>}
      <FieldError error={error} />
      <label>
        Institution name
        <input
          maxLength={200}
          onChange={(event) => setName(event.target.value)}
          required
          value={name}
        />
      </label>
      <label>
        Institution code
        <input
          maxLength={40}
          onChange={(event) => setCode(event.target.value)}
          required
          value={code}
        />
      </label>
      <label>
        Time zone
        <input
          maxLength={64}
          onChange={(event) => setTimezone(event.target.value)}
          required
          value={timezone}
        />
      </label>
      <label className="check-field">
        <input
          checked={active}
          onChange={(event) => setActive(event.target.checked)}
          type="checkbox"
        />{" "}
        Institution active
      </label>
      <div className="button-row">
        <button disabled={busy} type="submit">
          {busy ? "Saving…" : "Save changes"}
        </button>
        <button className="secondary-button" onClick={onRefresh} type="button">
          Reload
        </button>
      </div>
    </form>
  );
}

export function ClassroomsPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [reload, refresh] = useReload();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<{
    count: number;
    next: string | null;
    previous: string | null;
    results: Classroom[];
  } | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!accessToken) return;
    try {
      const result = await infrastructureApi.classrooms(accessToken, {
        search,
        is_active: filter === "" ? undefined : filter === "active",
        page,
      });
      setData(result);
      setError(null);
    } catch (cause) {
      setError(cause);
    } finally {
      setLoading(false);
    }
  }, [accessToken, filter, page, search]);

  useEffect(() => {
    void Promise.resolve().then(load);
  }, [load, reload]);

  async function create(input: ClassroomInput) {
    if (!accessToken) return;
    const classroom = await infrastructureApi.createClassroom(accessToken, input);
    navigate(`/admin/classrooms/${classroom.id}`);
  }

  return (
    <section className="content-page">
      <PageTitle
        title="Classrooms"
        description="Persistent physical rooms belonging to this institution."
      />
      <div className="resource-columns">
        <div>
          <div className="toolbar">
            <label>
              Search classrooms
              <input
                onChange={(event) => {
                  setLoading(true);
                  setPage(1);
                  setSearch(event.target.value);
                }}
                placeholder="Room code or name"
                value={search}
              />
            </label>
            <label>
              Status
              <select
                onChange={(event) => {
                  setLoading(true);
                  setPage(1);
                  setFilter(event.target.value);
                }}
                value={filter}
              >
                <option value="">All</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </label>
          </div>
          {loading && <p role="status">Loading classrooms…</p>}
          {error !== null && <Notice>{requestError(error)}</Notice>}
          {!loading && data && data.results.length === 0 && (
            <p className="empty-state">No classrooms match this view.</p>
          )}
          {!loading && data && data.results.length > 0 && (
            <>
              <ul className="resource-list">
                {data.results.map((room) => (
                  <li key={room.id}>
                    <Link to={`/admin/classrooms/${room.id}`}>
                      <strong>{room.code}</strong>
                      <span>{room.name || "No display name"}</span>
                      <span className={room.is_active ? "status-active" : "status-inactive"}>
                        {room.is_active ? "Active" : "Inactive"}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
              <div className="pagination-row">
                <span>{data.count} classroom(s)</span>
                <button
                  className="secondary-button"
                  disabled={!data.previous}
                  onClick={() => {
                    setLoading(true);
                    setPage((value) => value - 1);
                  }}
                  type="button"
                >
                  Previous
                </button>
                <button
                  className="secondary-button"
                  disabled={!data.next}
                  onClick={() => {
                    setLoading(true);
                    setPage((value) => value + 1);
                  }}
                  type="button"
                >
                  Next
                </button>
              </div>
            </>
          )}
          <button
            className="secondary-button"
            onClick={() => {
              setLoading(true);
              refresh();
            }}
            type="button"
          >
            Refresh list
          </button>
        </div>
        <section className="form-panel">
          <h2>Add classroom</h2>
          <ClassroomForm onSubmit={create} submitLabel="Create classroom" />
        </section>
      </div>
    </section>
  );
}

export function ClassroomDetailPage() {
  const { id = "" } = useParams();
  const { accessToken } = useAuth();
  const [reload, refresh] = useReload();
  const [classroom, setClassroom] = useState<Classroom | null>(null);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;
    let active = true;
    Promise.all([
      infrastructureApi.classroom(accessToken, id),
      infrastructureApi.cameras(accessToken, { classroom_id: id }),
    ])
      .then(([room, cameraPage]) => {
        if (active) {
          setClassroom(room);
          setCameras(cameraPage.results);
          setError(null);
        }
      })
      .catch((cause: unknown) => active && setError(cause))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [accessToken, id, reload]);

  async function save(input: ClassroomInput) {
    if (!accessToken) return;
    await infrastructureApi.updateClassroom(accessToken, id, input);
    setSuccess("Classroom details saved.");
    setLoading(true);
    refresh();
  }

  return (
    <section className="content-page">
      <Link className="back-link" to="/admin/classrooms">
        ← Classrooms
      </Link>
      {loading && <p role="status">Loading classroom…</p>}
      {error !== null && <Notice>{requestError(error)}</Notice>}
      {success && <Notice kind="success">{success}</Notice>}
      {!loading && classroom && (
        <>
          <PageTitle
            title={classroom.code}
            description={`${classroom.institution.name} · ${classroom.name || "Physical classroom"}`}
          />
          <div className="resource-columns">
            <section className="form-panel">
              <h2>Edit classroom</h2>
              <ClassroomForm initial={classroom} onSubmit={save} submitLabel="Save classroom" />
            </section>
            <section className="form-panel">
              <div className="section-heading">
                <h2>Cameras</h2>
                <Link className="button-link" to={`/admin/cameras?classroom_id=${classroom.id}`}>
                  Register camera
                </Link>
              </div>
              {cameras.length === 0 ? (
                <p className="empty-state">No cameras are registered in this classroom.</p>
              ) : (
                <ul className="resource-list">
                  {cameras.map((camera) => (
                    <li key={camera.id}>
                      <Link to={`/admin/cameras/${camera.id}`}>
                        <strong>{camera.code}</strong>
                        <span>{camera.display_name}</span>
                        <span
                          className={
                            camera.status === "ACTIVE" ? "status-active" : "status-inactive"
                          }
                        >
                          {camera.status}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </section>
  );
}

export function CamerasPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialClassroomId = searchParams.get("classroom_id") ?? "";
  const [reload, refresh] = useReload();
  const [search, setSearch] = useState("");
  const [classroomId, setClassroomId] = useState(initialClassroomId);
  const [status, setStatus] = useState("");
  const [pageNumber, setPageNumber] = useState(1);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [cameraCount, setCameraCount] = useState(0);
  const [cameraNext, setCameraNext] = useState<string | null>(null);
  const [cameraPrevious, setCameraPrevious] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!accessToken) return;
    try {
      const [roomPage, cameraPage] = await Promise.all([
        infrastructureApi.classrooms(accessToken, { page_size: 100 }),
        infrastructureApi.cameras(accessToken, {
          classroom_id: classroomId || undefined,
          search,
          status: status || undefined,
          page: pageNumber,
        }),
      ]);
      setClassrooms(roomPage.results);
      setCameras(cameraPage.results);
      setCameraCount(cameraPage.count);
      setCameraNext(cameraPage.next);
      setCameraPrevious(cameraPage.previous);
      setError(null);
    } catch (cause) {
      setError(cause);
    } finally {
      setLoading(false);
    }
  }, [accessToken, classroomId, pageNumber, search, status]);

  useEffect(() => {
    void Promise.resolve().then(load);
  }, [load, reload]);

  async function create(input: CameraInput) {
    if (!accessToken) return;
    const camera = await infrastructureApi.createCamera(accessToken, input);
    navigate(`/admin/cameras/${camera.id}`);
  }

  return (
    <section className="content-page">
      <PageTitle
        title="Cameras"
        description="Registered camera metadata only. Active does not indicate an online CCTV connection."
      />
      <div className="resource-columns">
        <div>
          <div className="toolbar">
            <label>
              Search cameras
              <input
                onChange={(event) => {
                  setLoading(true);
                  setPageNumber(1);
                  setSearch(event.target.value);
                }}
                placeholder="Camera code or display name"
                value={search}
              />
            </label>
            <label>
              Classroom
              <select
                onChange={(event) => {
                  setLoading(true);
                  setPageNumber(1);
                  setClassroomId(event.target.value);
                }}
                value={classroomId}
              >
                <option value="">All classrooms</option>
                {classrooms.map((room) => (
                  <option key={room.id} value={room.id}>
                    {room.code}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Status
              <select
                onChange={(event) => {
                  setLoading(true);
                  setPageNumber(1);
                  setStatus(event.target.value);
                }}
                value={status}
              >
                <option value="">All</option>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
              </select>
            </label>
          </div>
          {loading && <p role="status">Loading cameras…</p>}
          {error !== null && <Notice>{requestError(error)}</Notice>}
          {!loading && cameras.length === 0 && (
            <p className="empty-state">No cameras match this view.</p>
          )}
          {!loading && cameras.length > 0 && (
            <ul className="resource-list">
              {cameras.map((camera) => (
                <li key={camera.id}>
                  <Link to={`/admin/cameras/${camera.id}`}>
                    <strong>{camera.code}</strong>
                    <span>
                      {camera.display_name} · {camera.classroom.code}
                    </span>
                    <span
                      className={camera.status === "ACTIVE" ? "status-active" : "status-inactive"}
                    >
                      {camera.status}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
          {!loading && cameraCount > 0 && (
            <div className="pagination-row">
              <span>{cameraCount} camera(s)</span>
              <button
                className="secondary-button"
                disabled={!cameraPrevious}
                onClick={() => {
                  setLoading(true);
                  setPageNumber((value) => value - 1);
                }}
                type="button"
              >
                Previous
              </button>
              <button
                className="secondary-button"
                disabled={!cameraNext}
                onClick={() => {
                  setLoading(true);
                  setPageNumber((value) => value + 1);
                }}
                type="button"
              >
                Next
              </button>
            </div>
          )}
          <button
            className="secondary-button"
            onClick={() => {
              setLoading(true);
              refresh();
            }}
            type="button"
          >
            Refresh list
          </button>
        </div>
        <section className="form-panel">
          <h2>Register camera</h2>
          {classrooms.length === 0 ? (
            <p className="empty-state">Create an active classroom before registering a camera.</p>
          ) : (
            <CameraForm
              classrooms={classrooms}
              initialClassroomId={initialClassroomId}
              onSubmit={create}
              submitLabel="Register camera"
            />
          )}
        </section>
      </div>
    </section>
  );
}

export function CameraDetailPage() {
  const { id = "" } = useParams();
  const { accessToken } = useAuth();
  const [reload, refresh] = useReload();
  const [camera, setCamera] = useState<Camera | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;
    let active = true;
    infrastructureApi
      .camera(accessToken, id)
      .then((result) => active && setCamera(result))
      .catch((cause: unknown) => active && setError(cause))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [accessToken, id, reload]);

  async function save(input: CameraInput) {
    if (!accessToken) return;
    await infrastructureApi.updateCamera(accessToken, id, input);
    setSuccess("Camera details saved.");
    setLoading(true);
    refresh();
  }

  return (
    <section className="content-page">
      <Link className="back-link" to="/admin/cameras">
        ← Cameras
      </Link>
      {loading && <p role="status">Loading camera…</p>}
      {error !== null && <Notice>{requestError(error)}</Notice>}
      {success && <Notice kind="success">{success}</Notice>}
      {!loading && camera && (
        <>
          <PageTitle
            title={camera.code}
            description={`${camera.classroom.code} · ${camera.display_name}`}
          />
          <section className="form-panel detail-panel">
            <p className="source-note">
              <strong>LOCAL_FILE</strong> is a configured source type only. College CCTV/NVR/VMS
              connectivity is not configured; status below is metadata status, not online status.
            </p>
            <CameraForm
              key={`${camera.id}-${reload}`}
              initial={camera}
              classrooms={[]}
              onSubmit={save}
              submitLabel="Save camera"
            />
          </section>
        </>
      )}
    </section>
  );
}

export function TeacherLandingPage() {
  return (
    <section className="content-page">
      <PageTitle
        title="Classroom Engagement Analytics"
        description="Teacher features will be introduced in a later phase."
      />
    </section>
  );
}
