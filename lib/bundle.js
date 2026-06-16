const fs = require('fs');
const path = require('path');
const { CompositeDisposable } = require('atom');
const SelectListView = require('atom-select-list');

const packageName = require('../package.json').name;
const shortName = packageName.split('-').slice(0, 3).join('-');
const baseName = packageName.split('-').slice(0, 1).join('-');

const options = require('./settings.json').config;

module.exports = {
  config: options,

  disposables: null,

  selectListViews: {},
  previouslyFocusedElement: null,

  isInPreviewMode: false,

  activate() {
    this.disposables = new CompositeDisposable();

    // Add Command Panel entries for every option in package config
    for (let option in options) {
      this.disposables.add(
        atom.config.onDidChange(`${packageName}.${option}`, () => {
          this.enableConfigTheme();
        }),
      );

      // If option is string make a selectListView, if boolean make a toggle
      switch (options[option].type) {
        case 'string':
          this.selectListViews[option] = {};

          this.selectListViews[option].selectListView = new SelectListView({
            items: [],
            initialSelectionIndex: 0,

            itemsClassList: 'mark-active',
            elementForItem: (item) => {
              const element = document.createElement('li');
              if (item === atom.config.get(`${packageName}.${option}`)) {
                element.classList.add('active');
              }
              element.textContent = item;
              return element;
            },

            didChangeSelection: (item) => {
              if (typeof item !== 'undefined') {
                this.enablePreviewTheme(option, item);
              }
            },
            didConfirmSelection: (item) => {
              if (
                typeof item !== 'undefined' &&
                item !== atom.config.get(`${packageName}.${option}`)
              ) {
                atom.config.set(`${packageName}.${option}`, item);
              }
              this.slv_hide(option);
            },
            didCancelSelection: () => {
              this.enableConfigTheme();
              this.slv_hide(option);
            },
          });

          this.disposables.add(
            atom.commands.add(
              'atom-workspace',
              `${shortName}:select-${this.getNormalizedName(options[option].title)}`,
              () => this.slv_show(option),
            ),
          );
          break;
        case 'boolean':
          this.disposables.add(
            atom.commands.add(
              'atom-workspace',
              `${shortName}:toggle-${this.getNormalizedName(options[option].title)}`,
              () => this.toggle(option),
            ),
          );
          break;
        default:
          console.log(
            `Warning! Entry of unknown type in settings.json: ${option}`,
          );
      }
    }

    // Add entry to reset settings
    this.disposables.add(
      atom.commands.add(
        'atom-workspace',
        `${shortName}:reset-to-default-theme`,
        this.unsetTheme,
      ),
    );
  },

  deactivate() {
    for (let option in this.selectListViews) {
      if (this.selectListViews[option].selectListView) {
        this.selectListViews[option].selectListView.destroy();
      }
      if (this.selectListViews[option].panel) {
        this.selectListViews[option].panel.destroy();
      }
    }
    this.disposables.dispose();
  },

  slv_show(option) {
    if (!this.selectListViews[option] || !this.selectListViews[option].panel) {
      this.selectListViews[option].panel = atom.workspace.addModalPanel({
        item: this.selectListViews[option].selectListView,
      });
    }

    const props = {
      items: options[option].enum,
      initialSelectionIndex: options[option].enum.indexOf(
        atom.config.get(`${packageName}.${option}`),
      ),
    };

    this.previouslyFocusedElement = document.activeElement;
    this.selectListViews[option].selectListView.update(props);
    this.selectListViews[option].panel.show();
    this.selectListViews[option].selectListView.focus();
  },

  slv_hide(option) {
    this.selectListViews[option].panel.hide();
    if (this.previouslyFocusedElement) {
      this.previouslyFocusedElement.focus();
      this.previouslyFocusedElement = null;
    }
  },

  toggle(option) {
    atom.config.set(
      `${packageName}.${option}`,
      !atom.config.get(`${packageName}.${option}`),
    );
  },

  getConfigTheme() {
    const configTheme = {};
    for (let option in options) {
      configTheme[option] = atom.config.get(`${packageName}.${option}`);
    }
    return configTheme;
  },

  unsetTheme() {
    for (let option in options) {
      if (
        atom.config.get(`${packageName}.${option}`) !== options[option].default
      ) {
        atom.config.unset(`${packageName}.${option}`);
      }
    }
  },

  getNormalizedName(name) {
    return `${name}`
      .replace(/\(/g, '')
      .replace(/\)/g, '')
      .replace(/,/g, '')
      .replace(/é/g, 'e')
      .replace(/ /g, '-')
      .toLowerCase();
  },

  enableConfigTheme() {
    const newTheme = this.getConfigTheme();
    this.enableTheme(newTheme, false);
  },

  enablePreviewTheme(option, value) {
    const newTheme = this.getConfigTheme();
    newTheme[option] = value;
    this.enableTheme(newTheme, true);
  },

  enableTheme(theme, isPreview) {
    try {
      // Write the requested theme to the `syntax-variables` file.
      const syntaxVariablesPath = path.join(
        __dirname,
        '..',
        'styles',
        `${baseName}-variables.less`,
      );

      let newFileContent = '';
      for (let option in options) {
        switch (options[option].type) {
          case 'string':
            newFileContent += `@${baseName}-${option}: '${this.getNormalizedName(theme[option])}';\n`;
            break;
          case 'boolean':
            newFileContent += `@${baseName}-${option}: ${theme[option]};\n`;
            break;
          default:
            console.log(
              `Warning! Entry of unknown type in settings.json: ${option}`,
            );
        }
      }

      // Only write to file if theme has changed.
      let isNew = false;
      const currentFileContent = fs.readFileSync(syntaxVariablesPath, 'utf8');
      if (currentFileContent !== newFileContent) {
        isNew = true;
        fs.writeFileSync(syntaxVariablesPath, newFileContent);
      }

      // Reload stylesheets.
      const activePackages = atom.packages.getActivePackages();
      if (activePackages.length === 0 || isPreview) {
        // Reload own stylesheets to apply the requested theme.
        if (isNew) {
          if (isPreview) {
            this.isInPreviewMode = true;
          }

          atom.packages.getLoadedPackage(`${packageName}`).reloadStylesheets();
        }
      } else if (isNew || this.isInPreviewMode) {
        // Reload the stylesheets of all packages to apply the requested theme.
        this.isInPreviewMode = false;

        for (let activePackage of activePackages) {
          activePackage.reloadStylesheets();
        }
      }
    } catch (error) {
      // If unsuccessfull enable the default theme.
      console.log('Error! Theme cannot be applied');
      console.log(error);
      this.unsetTheme();
    }
  },
};
