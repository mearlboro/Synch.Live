import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = [ "close" ]

  connect() {
      this.closeTarget.hidden = false
  }

  hide() {
      this.element.remove()
  }
}
