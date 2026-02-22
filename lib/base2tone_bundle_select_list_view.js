/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/main/docs/suggestions.md
 */
const {SelectListView} = require('atom-space-pen-views');

class Base2ToneBundleSelectListView extends SelectListView {

  initialize(base2tone) {
    this.base2tone = base2tone;
    super.initialize(...arguments);
    this.list.addClass('mark-active');
    return this.setItems(this.getThemes());
  }

  viewForItem(theme) {
    const element = document.createElement('li');
    if (this.base2tone.isConfigTheme(theme.scheme, theme.contrastGutter, theme.style)) {
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
    this.base2tone.isPreview = true;
    if (this.attached) { return this.base2tone.enableTheme(theme.scheme, theme.contrastGutter, theme.style); }
  }

  confirmed(theme) {
    this.confirming = true;
    this.base2tone.isPreview = false;
    this.base2tone.isPreviewConfirmed = true;
    this.base2tone.setThemeConfig(theme.scheme, theme.contrastGutter, theme.style);
    this.cancel();
    return this.confirming = false;
  }

  cancel() {
    super.cancel(...arguments);
    if (!this.confirming) { this.base2tone.enableConfigTheme(); }
    this.base2tone.isPreview = false;
    return this.base2tone.isPreviewConfirmed = false;
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
    const schemes = atom.config.getSchema(`${this.base2tone.packageName}.scheme`).enum;
    const contrastGutter = atom.config.get(`${this.base2tone.packageName}.contrastGutter`);
    const style = atom.config.get(`${this.base2tone.packageName}.style`);
    const themes = [];
    schemes.forEach(scheme => themes.push({scheme, contrastGutter, style, name: `${scheme}`}));
    return themes;
  }
}

module.exports = Base2ToneBundleSelectListView;
