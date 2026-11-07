const dropdownContainers = document.querySelectorAll(".multiselect-container");
const filterForm = document.forms.filters;
const filtersSection = document.getElementById("filters");
let filtersChanged = false;

dropdownContainers.forEach(container => {
  const header = container.querySelector(".combo-header");
  const textbox = container.querySelector(".display-textbox");
  const hiddenInput = container.querySelector(".hidden-ids-input");
  const master = container.querySelector(".master-checkbox"); // Optional
  const children = [...container.querySelectorAll(".child-checkbox")];
  const searchInput = container.querySelector(".dropdown-search");

  header.addEventListener("click", event => {
    dropdownContainers.forEach(other => {
      if (other !== container) {
        other.classList.remove("open");
      }
    });

    container.classList.toggle("open");
    event.stopPropagation();
  });

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const searchTerm = searchInput.value.trim().toLowerCase();

      container.querySelectorAll(".option-item").forEach(option => {
        const isMaster = option.querySelector(".master-checkbox");
        const matches = option.textContent.toLowerCase().includes(searchTerm);

        option.style.display = isMaster || matches ? "" : "none";
      });
    });
  }

  function updateSelection() {
    if (master && master.checked) {
      children.forEach(child => {
        child.checked = false;
      });

      textbox.value = "";
      hiddenInput.value = "";
      return;
    }

    const selected = children.filter(child => child.checked);

    textbox.value = selected.map(child => child.value).join(", ");
    hiddenInput.value = selected.map(child => child.dataset.id).join(",");
  }

  if (master) {
    master.addEventListener("change", () => {
      updateSelection();
      filtersChanged = true;
    });
  }

  children.forEach(child => {
    child.addEventListener("change", () => {
      if (master && child.checked) {
        master.checked = false;
      }

      updateSelection();
      filtersChanged = true;
    });
  });

  updateSelection();
});

// Track changes to other filter fields, such as dates or regular selects.
// Search boxes and display/hidden fields do not trigger form submission.
filterForm
  .querySelectorAll(
    'input:not(.display-textbox):not(.hidden-ids-input):not(.dropdown-search):not([type="checkbox"]), select'
  )
  .forEach(field => {
    field.addEventListener("change", () => {
      filtersChanged = true;
    });
  });

// Close dropdowns on outside clicks.
// Submit changed filters when clicking outside the filter section.
document.addEventListener("click", event => {
  dropdownContainers.forEach(container => {
    if (!container.contains(event.target)) {
      container.classList.remove("open");
    }
  });

  const clickedOutsideFilters =
    filtersSection && !filtersSection.contains(event.target);

  if (clickedOutsideFilters && filtersChanged) {
    filtersChanged = false;
    filterForm.requestSubmit();
  }
});