# api.py — FastAPI REST API for civil information system
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import db_ali as db
import io

db.init_db()

app = FastAPI(title="المعلومات المدنية للمواطنين API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auth ───

class LoginReq(BaseModel):
    username: str
    password: str

class ChangePwReq(BaseModel):
    old_password: str
    new_password: str

class AddUserReq(BaseModel):
    username: str
    password: str
    display_name: str
    role: str = "viewer"

@app.post("/api/auth/login")
def login(req: LoginReq):
    user = db.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(401, "اسم المستخدم أو كلمة المرور غير صحيحة")
    return {"user": {k: user[k] for k in ("id", "username", "display_name", "role")}}

@app.post("/api/auth/change-password/{user_id}")
def change_password(user_id: int, req: ChangePwReq):
    user = db.authenticate_by_id_and_password(user_id, req.old_password) if hasattr(db, 'authenticate_by_id_and_password') else None
    if not user:
        users = db.get_users()
        u = next((u for u in users if u["id"] == user_id), None)
        if u and db.authenticate(u["username"], req.old_password):
            db.update_password(user_id, req.new_password)
            return {"ok": True}
        raise HTTPException(400, "كلمة المرور الحالية غير صحيحة")
    db.update_password(user_id, req.new_password)
    return {"ok": True}

@app.get("/api/users")
def list_users():
    return db.get_users()

@app.post("/api/users")
def create_user(req: AddUserReq):
    uid = db.add_user(req.username, req.password, req.display_name, req.role)
    if not uid:
        raise HTTPException(400, "اسم المستخدم موجود مسبقاً")
    return {"id": uid}

@app.delete("/api/users/{user_id}")
def remove_user(user_id: int):
    if not db.delete_user(user_id):
        raise HTTPException(400, "لا يمكن حذف هذا المستخدم")
    return {"ok": True}


# ─── Stats ───

@app.get("/api/stats")
def stats():
    return db.get_stats()

@app.get("/api/stats/distribution/{col}")
def distribution(col: str, limit: int = 30):
    allowed = {"المنطقة", "الحي", "المهنة", "الحالة_الزوجية", "القضاء"}
    if col not in allowed:
        raise HTTPException(400, f"عمود غير مسموح: {col}")
    return db.get_distribution(col, limit)


# ─── Persons ───

class PersonReq(BaseModel):
    name: str = ""
    birth: str = ""
    job: str = ""
    qadha: str = ""
    address: str = ""
    mahal: str = ""
    phone: str = ""
    region: str = ""
    hay: str = ""
    mukhtar_id: Optional[int] = None
    marital_status: str = ""
    sila: str = ""

@app.get("/api/persons")
def list_persons(
    search: str = "",
    region: str = "",
    haya: str = "",
    mihna: str = "",
    mukhtar_id: Optional[int] = None,
    deleted_filter: str = "active",
    limit: int = 50,
    offset: int = 0,
):
    rows, total = db.get_persons(
        search=search, region=region, haya=haya, mihna=mihna,
        mukhtar_id=mukhtar_id, deleted_filter=deleted_filter,
        limit=limit, offset=offset,
    )
    return {"rows": rows, "total": total}

@app.get("/api/persons/{pid}")
def get_person(pid: int):
    p = db.get_person(pid)
    if not p:
        raise HTTPException(404, "السجل غير موجود")
    return p

@app.put("/api/persons/{pid}")
def update_person(pid: int, req: PersonReq):
    dups = db.find_duplicate_persons(req.name, exclude_id=pid)
    if dups:
        raise HTTPException(400, f"يوجد تكرار في الاسم: التسلسل {dups[0]['id']}")
    ok = db.update_person(
        pid, الاسم=req.name, التولد=req.birth, المهنة=req.job,
        القضاء=req.qadha, العنوان=req.address, المحل=req.mahal,
        الهاتف=req.phone, المنطقة=req.region, الحي=req.hay,
        mukhtar_id=req.mukhtar_id, الحالة_الزوجية=req.marital_status,
        الصلة=req.sila,
    )
    return {"ok": ok}

@app.post("/api/persons")
def add_person(req: PersonReq):
    if not req.name.strip():
        raise HTTPException(400, "الاسم مطلوب")
    dups = db.find_duplicate_persons(req.name)
    if dups:
        raise HTTPException(400, f"يوجد تكرار في الاسم: التسلسل {dups[0]['id']}")
    new_id = db.add_person(
        الاسم=req.name, التولد=req.birth, المهنة=req.job,
        القضاء=req.qadha or req.region, العنوان=req.address,
        المحل=req.mahal, الهاتف=req.phone, الشيت="يدوي",
        المنطقة=req.region, الحي=req.hay, mukhtar_id=req.mukhtar_id,
        الحالة_الزوجية=req.marital_status, الصلة=req.sila,
    )
    if req.hay and req.region:
        db.add_neighborhood(req.hay, req.region)
    return {"id": new_id}

@app.delete("/api/persons/{pid}")
def delete_person(pid: int):
    return {"ok": db.soft_delete(pid)}

@app.post("/api/persons/{pid}/restore")
def restore_person(pid: int):
    return {"ok": db.restore(pid)}

@app.get("/api/persons/export/excel")
def export_excel(
    search: str = "", region: str = "", haya: str = "",
    mihna: str = "", mukhtar_id: Optional[int] = None,
    deleted_filter: str = "active",
):
    data = db.export_to_excel(search, region, haya, mihna, mukhtar_id, deleted_filter)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=export.xlsx"},
    )


# ─── Mukhtars ───

class MukhtarReq(BaseModel):
    name: str
    phone: str = ""
    neighborhood_ids: list[int] = []

@app.get("/api/mukhtars")
def list_mukhtars():
    return db.get_mukhtars()

@app.get("/api/mukhtars/grouped")
def mukhtars_grouped():
    return db.get_mukhtars_grouped_by_region()

@app.get("/api/mukhtars/{mid}")
def get_mukhtar(mid: int):
    m = db.get_mukhtar(mid)
    if not m:
        raise HTTPException(404)
    return m

@app.post("/api/mukhtars")
def create_mukhtar(req: MukhtarReq):
    dup = db.find_duplicate_mukhtar(req.name)
    if dup:
        raise HTTPException(400, "مختار مكرر")
    mid = db.add_mukhtar(req.name, req.phone)
    if req.neighborhood_ids:
        db.set_mukhtar_neighborhoods(mid, req.neighborhood_ids)
    return {"id": mid}

@app.put("/api/mukhtars/{mid}")
def edit_mukhtar(mid: int, req: MukhtarReq):
    dup = db.find_duplicate_mukhtar(req.name, exclude_id=mid)
    if dup:
        raise HTTPException(400, "مختار مكرر")
    db.update_mukhtar(mid, req.name, req.phone)
    db.set_mukhtar_neighborhoods(mid, req.neighborhood_ids)
    return {"ok": True}

@app.delete("/api/mukhtars/{mid}")
def remove_mukhtar(mid: int):
    return {"ok": db.delete_mukhtar(mid)}


# ─── Neighborhoods ───

class NeighborhoodReq(BaseModel):
    name: str
    region: str

@app.get("/api/neighborhoods")
def list_neighborhoods(region: str = ""):
    return db.get_neighborhoods(region)

@app.post("/api/neighborhoods")
def create_neighborhood(req: NeighborhoodReq):
    dup = db.find_duplicate_neighborhood(req.name, req.region)
    if dup:
        raise HTTPException(400, f"الحي موجود مسبقاً في {req.region}")
    nid = db.add_neighborhood(req.name, req.region)
    if not nid:
        raise HTTPException(400, "فشل الإضافة")
    return {"id": nid}

@app.delete("/api/neighborhoods/{nid}")
def remove_neighborhood(nid: int):
    return {"ok": db.delete_neighborhood(nid)}

@app.get("/api/regions")
def list_regions():
    return db.MAIN_REGIONS

@app.get("/api/hayas/{region}")
def hayas_for_region(region: str):
    return db.get_hayas_for_region(region)


# ─── Family ───

@app.get("/api/family/{family_id}")
def family_members(family_id: int):
    return db.get_family_members(family_id)

@app.post("/api/family/create/{pid}")
def create_family(pid: int):
    fid = db.create_family(pid)
    return {"family_id": fid}

@app.post("/api/family/link/{pid}")
def link_family(pid: int, family_id: int, sila: str = "أخرى"):
    return {"ok": db.link_to_family(pid, family_id, sila)}

@app.post("/api/family/unlink/{pid}")
def unlink_family(pid: int):
    return {"ok": db.unlink_from_family(pid)}


# ─── Backup ───

@app.get("/api/backups")
def list_backups():
    return [{"name": b["name"], "size_mb": round(b["size_mb"], 2), "date": b["date"]}
            for b in db.get_backups()]

@app.post("/api/backups/create")
def create_backup():
    bp = db.create_backup()
    if not bp:
        raise HTTPException(400, "لا توجد قاعدة بيانات")
    return {"name": bp.name}

@app.post("/api/backups/restore")
def restore_bk(name: str):
    backups = db.get_backups()
    bk = next((b for b in backups if b["name"] == name), None)
    if not bk:
        raise HTTPException(404)
    db.create_backup()
    db.restore_backup(bk["path"])
    return {"ok": True}

@app.delete("/api/backups/{name}")
def delete_bk(name: str):
    backups = db.get_backups()
    bk = next((b for b in backups if b["name"] == name), None)
    if not bk:
        raise HTTPException(404)
    db.delete_backup(bk["path"])
    return {"ok": True}

@app.post("/api/backups/cleanup")
def cleanup_backups(days: int = 30):
    n = db.cleanup_old_backups(days)
    return {"deleted": n}


# ─── Lookup ───

@app.get("/api/lookup/marital-status")
def marital_statuses():
    return db.MARITAL_STATUS

@app.get("/api/lookup/family-relations")
def family_relations():
    return db.FAMILY_RELATIONS

@app.get("/api/lookup/roles")
def roles():
    return db.ROLES
