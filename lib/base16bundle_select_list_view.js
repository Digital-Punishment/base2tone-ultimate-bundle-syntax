/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/main/docs/suggestions.md
 */
const {SelectListView} = require('atom-space-pen-views');

class Base16BundleSelectListView extends SelectListView {

  initialize(base16) {
    this.base16 = base16;
    super.initialize(...arguments);
    this.list.addClass('mark-active');
    return this.setItems(this.getThemes());
  }

  viewForItem(theme) {
    const element = document.createElement('li');
    if (this.base16.isConfigTheme(theme.scheme, theme.invertColors)) {
      element.classList.add('active');
    }
    element.textContent = theme.name;
    return element;
  }

  getFilterKey() {
    return 'name';
  }

  selectItemView(view) {
    super.selectItemView(...arguments);
    const theme = this.getSelectedItem();
    this.base16.isPreview = true;
    if (this.attached) { return this.base16.enableTheme(theme.scheme, theme.invertColors); }
  }

  confirmed(theme) {
    this.confirming = true;
    this.base16.isPreview = false;
    this.base16.isPreviewConfirmed = true;
    this.base16.setThemeConfig(theme.scheme, theme.invertColors);
    this.cancel();
    return this.confirming = false;
  }

  cancel() {
    super.cancel(...arguments);
    if (!this.confirming) { this.base16.enableConfigTheme(); }
    this.base16.isPreview = false;
    return this.base16.isPreviewConfirmed = false;
  }

  cancelled() {
    return (this.panel != null ? this.panel.destroy() : undefined);
  }

  attach() {
    if (this.panel == null) { this.panel = atom.workspace.addModalPanel({item: this}); }
    this.selectItemView(this.list.find('li:last'));
    this.selectItemView(this.list.find('.active'));
    this.focusFilterEditor();
    return this.attached = true;
  }

  getThemes() {
    const schemes = atom.config.getSchema(`${this.base16.packageName}.scheme`).enum;
    const invertColors = atom.config.get(`${this.base16.packageName}.invertColors`)
    const themes = [];
    schemes.forEach(scheme => themes.push({scheme, invertColors, name: `${scheme}`}));
    return themes;
  }
}

module.exports = Base16BundleSelectListView;
