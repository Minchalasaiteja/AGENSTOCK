from bson import ObjectId
from app.routes.users import convert_objectid


def test_convert_objectid_simple():
    obj = {"_id": ObjectId(), "nested": {"id": ObjectId()}}
    converted = convert_objectid(obj)
    assert isinstance(converted["_id"], str)
    assert isinstance(converted["nested"]["id"], str)


def test_convert_objectid_list():
    arr = [{"_id": ObjectId()}, {"_id": ObjectId()}]
    converted = convert_objectid(arr)
    assert all(isinstance(x["_id"], str) for x in converted)
