import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = [ "pulse", "dot" ]
  static classes = [ "connectedPulse", "connectedDot", "disconnectedPulse", "disconnectedDot" ]

  connect() {
      this.element.hidden = false
      Turbo.session.streamObserver.sources
      this.pulseTarget.classList.replace(this.connectedPulseClass, this.disconnectedPulseClass)
      this.dotTarget.classList.replace(this.connectedDotClass, this.disconnectedDotClass)
  }

  disconnect() {
      this.element.hidden = true
  }
}
