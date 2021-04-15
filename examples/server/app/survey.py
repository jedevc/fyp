from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from sqlalchemy import Boolean, Column, Enum, Integer, String

from .database import Base, Session, engine


def to_camel_case(s: str) -> str:
    parts = s.replace("-", " ").replace("_", " ").split(" ")
    return "".join(p.capitalize() for p in parts)


class Field:
    def __init__(self, name: str, required: bool = False):
        self.name = name
        self.required = required

    def translate(self, value: Any) -> Any:
        return value

    def make_column(self) -> Column:
        return Column(String, nullable=not self.required)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} required={self.required}>"


class CheckboxField(Field):
    def __init__(self, name: str):
        super().__init__(name)

    def translate(self, value: Any) -> Any:
        return bool(value)

    def make_column(self) -> Column:
        return Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"


class RadioField(Field):
    def __init__(self, name: str, options: List[str], required: bool = False):
        super().__init__(name, required)
        self.options = options

    def add_option(self, option: str):
        self.options.append(option)

    def make_column(self) -> Column:
        return Column(
            Enum(*self.options, name=f"{self.name}-enum"), nullable=not self.required
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} options={self.options} required={self.required}>"


def _create_fields(path: Path) -> Dict[str, Field]:
    text = path.read_text()
    soup = BeautifulSoup(text, "html.parser")

    fields: Dict[str, Field] = {}

    for el in soup.find_all(["input", "textarea", "select"]):
        name = el["name"]
        if not name:
            continue

        if name in fields:
            field = fields[name]
            if isinstance(field, RadioField):
                field.add_option(el["value"])
            else:
                raise RuntimeError("cannot merge non-radio fields")
        else:
            required = "required" in el.attrs
            if el.name == "select":
                options = [item["value"] for item in el.find_all("option")]
                fields[name] = RadioField(name, options)
            elif el.get("type") == "checkbox":
                fields[name] = CheckboxField(name)
            elif el.get("type") == "radio":
                fields[name] = RadioField(name, [el["value"]], required=required)
            else:
                fields[name] = Field(name, required=required)

    return fields


def _create_model(fields: Dict[str, Field]) -> Any:
    survey_fields = {}
    survey_fields["__tablename__"] = "surveys"
    survey_fields["id"] = Column(Integer, primary_key=True)
    survey_fields.update(
        {to_camel_case(field.name): field.make_column() for field in fields.values()}
    )
    return type("Survey", (Base,), survey_fields)


SURVEY_PATH = Path(__file__).parent.parent / "templates" / "survey.html"
FIELDS: Dict[str, Field] = _create_fields(SURVEY_PATH)

Survey = _create_model(FIELDS)
Base.metadata.create_all(engine)


def submit(form: Dict[str, Any]):
    form = {**form}
    session = Session()

    for field_name in form:
        if field_name in FIELDS:
            form[field_name] = FIELDS[field_name].translate(form[field_name])
        else:
            raise KeyError(f"unknown field name {field_name}")

    form = {to_camel_case(field): value for field, value in form.items()}
    survey = Survey(**form)
    session.add(survey)
    session.commit()
