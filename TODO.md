# TODO
### Branches of development:
* Core
  * Add proper candidate filtering (initial phase, rule out oblivious inadequate candidates)
  * Find a way to objectively rank candidates
    * Approach 1: Classic elimination process, this only works for 1 candidate
    * Approach 2: Linked list of candidates created based on comparison to other candidates.
    * Approach 3: -
* Frontend
  * HR panel
    * Login, company account, personal account
    * Process monitoring
    * Run batch comparison at will
  * Candidate interface
    * Get invited the experience
    * Get served all the questions one by one
    * Capture video, send to backend
* Backend
  * Create FastAPI server, serve basic frontend
  * Create a working Rest API
  * Create separation of videos by company
* Other
  * Email candidates inviting them to partake in the evaluation
