const API_URL = "http://127.0.0.1:8000";

async function requestJSON(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || `Request failed with status ${response.status}`);
  }

  return data;
}

function normalizedKey(key) {
  return key.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function findValue(record, names) {
  if (!record || typeof record !== "object") return "";
  const keys = Object.keys(record);
  const wanted = names.map(normalizedKey);
  const key = keys.find(candidate => wanted.includes(normalizedKey(candidate)));
  return key ? record[key] : "";
}

function labelFor(key) {
  return key
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, character => character.toUpperCase());
}

function valueFor(value) {
  if (value === null || value === undefined || value === "") return "";
  if (Array.isArray(value)) return value.map(valueFor).filter(Boolean).join(" · ");
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, item]) => `${labelFor(key)}: ${valueFor(item)}`)
      .filter(Boolean)
      .join(" · ");
  }
  return String(value);
}

function addField(list, key, value) {
  const text = valueFor(value);
  if (!text) return;

  const row = document.createElement("div");
  row.className = "detail-row";

  const term = document.createElement("dt");
  term.textContent = labelFor(key);
  const description = document.createElement("dd");
  description.textContent = text;

  row.append(term, description);
  list.appendChild(row);
}

function renderProfile(profile) {
  const name = findValue(profile, ["name", "full_name", "fullname"]);
  const headline = findValue(profile, ["headline", "title", "role", "job_title"]);
  const summary = findValue(profile, ["summary", "profile_summary", "about"]);
  const excluded = new Set([
    "name", "fullname", "headline", "title", "role", "jobtitle",
    "summary", "profilesummary", "about"
  ]);

  document.getElementById("profile-name").textContent = valueFor(name) || "Resume";
  document.getElementById("profile-headline").textContent = valueFor(headline);
  document.getElementById("profile-summary").textContent = valueFor(summary);
  document.getElementById("profile-headline").hidden = !headline;
  document.getElementById("profile-summary").hidden = !summary;

  const details = document.getElementById("profile-details");
  details.replaceChildren();
  Object.entries(profile || {}).forEach(([key, value]) => {
    if (!excluded.has(normalizedKey(key))) addField(details, key, value);
  });
  details.hidden = details.childElementCount === 0;
}

function renderSummary(summary) {
  const section = document.getElementById("summary-section");
  const content = document.getElementById("summary-content");
  content.replaceChildren();

  if (!summary || typeof summary !== "object") {
    section.hidden = true;
    return;
  }

  Object.entries(summary).forEach(([key, value]) => {
    if (value === null || value === undefined || typeof value === "object") return;
    const metric = document.createElement("div");
    metric.className = "metric";
    const number = document.createElement("strong");
    number.textContent = valueFor(value);
    const label = document.createElement("span");
    label.textContent = labelFor(key);
    metric.append(number, label);
    content.appendChild(metric);
  });

  section.hidden = content.childElementCount === 0;
}

function makeTagList(values) {
  const tags = document.createElement("ul");
  tags.className = "tag-list";
  values.forEach(value => {
    const text = valueFor(value);
    if (!text) return;
    const tag = document.createElement("li");
    tag.textContent = text;
    tags.appendChild(tag);
  });
  return tags;
}

function renderRecords(sectionName, records) {
  const section = document.getElementById(`${sectionName}-section`);
  const content = document.getElementById(`${sectionName}-content`);
  content.replaceChildren();

  if (!Array.isArray(records) || records.length === 0) {
    section.hidden = true;
    return;
  }

  if (sectionName === "skills") {
    const skillValues = records.map(record =>
      typeof record === "object" && record !== null
        ? findValue(record, ["skill", "name", "skill_name"])
        : record
    );
    content.appendChild(makeTagList(skillValues));
    section.hidden = content.firstElementChild.childElementCount === 0;
    return;
  }

  const titleKeys = {
    experience: ["job_title", "title", "role", "position", "company", "employer", "name"],
    projects: ["project_name", "name", "title", "project"],
    education: ["degree", "qualification", "program", "institution", "school", "name"],
    awards: ["award_name", "award", "title", "name"]
  }[sectionName] || ["title", "name"];

  records.forEach((record, index) => {
    const card = document.createElement("article");
    card.className = "resume-item";
    const title = document.createElement("h3");
    title.textContent = valueFor(findValue(record, titleKeys)) || `${labelFor(sectionName)} ${index + 1}`;
    card.appendChild(title);

    if (!record || typeof record !== "object" || Array.isArray(record)) {
      const text = document.createElement("p");
      text.textContent = valueFor(record);
      card.appendChild(text);
    } else {
      const skills = findValue(record, ["skills"]);
      if (Array.isArray(skills) && skills.length) {
        card.appendChild(makeTagList(skills));
      }

      const details = document.createElement("dl");
      Object.entries(record).forEach(([key, value]) => {
        if (["id", "projectid", "skills"].includes(normalizedKey(key))) return;
        if (value !== null && typeof value === "object" && !Array.isArray(value)) {
          addField(details, key, value);
        } else if (Array.isArray(value)) {
          addField(details, key, value);
        } else {
          addField(details, key, value);
        }
      });
      if (details.childElementCount) card.appendChild(details);
    }

    content.appendChild(card);
  });

  section.hidden = content.childElementCount === 0;
}

function renderResume(resume) {
  renderProfile(resume.profile || {});
  renderSummary(resume.summary);
  ["experience", "projects", "skills", "education", "awards"].forEach(section => {
    renderRecords(section, resume[section]);
  });

  const generatedAt = document.getElementById("generated-at");
  generatedAt.textContent = resume.generated_at
    ? `Resume data updated ${valueFor(resume.generated_at)}`
    : "";
  document.getElementById("resume-sheet").hidden = false;
}

function renderAwards(container, awards) {
  container.replaceChildren();
  if (!Array.isArray(awards) || awards.length === 0) {
    container.textContent = "No awards available.";
    return;
  }

  const list = document.createElement("ul");
  awards.forEach(award => {
    const item = document.createElement("li");
    item.textContent = typeof award === "object"
      ? Object.entries(award).map(([key, value]) => `${labelFor(key)}: ${valueFor(value)}`).join(" · ")
      : valueFor(award);
    list.appendChild(item);
  });
  container.appendChild(list);
}

document.addEventListener("DOMContentLoaded", () => {
  const resumeSheet = document.getElementById("resume-sheet");
  const status = document.getElementById("status");
  const printButton = document.getElementById("print-button");

  if (resumeSheet) {
    requestJSON(`${API_URL}/api/resume`)
      .then(data => {
        renderResume(data);
        status.textContent = "";
      })
      .catch(error => {
        status.textContent = `Could not load resume: ${error.message}`;
        status.classList.add("error");
      });
  }

  if (printButton) {
    printButton.addEventListener("click", () => window.print());
  }

  const awardsButton = document.getElementById("awardsBtn");
  const awardsContainer = document.getElementById("awardsContainer");
  if (awardsButton && awardsContainer) {
    awardsButton.addEventListener("click", async () => {
      awardsContainer.textContent = "Loading awards...";
      try {
        const resume = await requestJSON(`${API_URL}/api/resume`);
        renderAwards(awardsContainer, resume.awards);
      } catch (error) {
        awardsContainer.textContent = `Could not load awards: ${error.message}`;
      }
    });
  }

  const contactForm = document.getElementById("contactForm");
  const formResponse = document.getElementById("formResponse");
  if (contactForm && formResponse) {
    contactForm.addEventListener("submit", async event => {
      event.preventDefault();
      formResponse.textContent = "Sending...";
      try {
        const result = await requestJSON(`${API_URL}/api/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: document.getElementById("name").value,
            email: document.getElementById("email").value,
            message: document.getElementById("message").value
          })
        });
        formResponse.textContent = `Message sent successfully! ID: ${result.id}`;
        contactForm.reset();
      } catch (error) {
        formResponse.textContent = `Could not send message: ${error.message}`;
      }
    });
  }
});

const docsBtn = document.getElementById("docsBtn");


if (docsBtn) {
    docsBtn.addEventListener("click", () => {
        window.open("http://127.0.0.1:8000/docs", "_blank");
    });
  }



































































  