(ns abaki.methods.analyze
  "abaki anti-monopoly observation and route-around policy analysis."
  (:require [kotoba.lang.text :as str]
            [abaki.methods.live-gate :as lg]
            #?(:clj [clojure.edn :as edn])
            #?(:clj [clojure.java.io :as io])))

(def weights
  {"closed_source_models" 30 "proprietary_hardware_lockin" 40
   "pricing_power_abuse" 30 "f1_hybrid_lockin" 40 "gene_patents" 30
   "lawsuits_against_farmers" 30 "warehouse_labor_exploitation" 50
   "market_share_dominance" 20 "anti_union_tactics" 30})

(defn calculate-ci [traits]
  (min 100 (reduce-kv (fn [score trait active]
                        (if (and active (contains? weights trait))
                          (+ score (get weights trait)) score))
                      0 traits)))

(defn publish-live
  ([routing-policy gate] (publish-live routing-policy gate nil))
  ([routing-policy gate env]
   (let [refused (try (lg/require-gate gate env) nil
                      (catch #?(:clj clojure.lang.ExceptionInfo :cljs :default) e
                        (if (= (:abaki.methods.live-gate/kind (ex-data e)) lg/live-gate-refused)
                          e (throw e))))]
     (if refused
       []
       (mapv (fn [blocked]
               {:db/id (get blocked "id")
                :abaki/status :non-aligned
                :abaki/ci-score (get blocked "reason_ci" 0)
                :abaki/attested-by (:operator-did gate)})
             (get routing-policy "blocked_entities" []))))))

(defn analyze [entities]
  (let [header ["# abaki: Chokepoint & Monopoly Visualization Report\n"
                "> **Objective**: Visualize monopolies and generate structural reactions (Route Around) to prevent dependency.\n\n"
                "## Identified Entities & Chokepoint Index (CI)\n"
                "| Entity | Domain | CI Score | Status | Primary Owners |"
                "|---|---|---|---|---|"]]
    (reduce
     (fn [{:keys [report-lines routing-policy]} entity]
       (let [ci (calculate-ci (get entity "traits"))
             blocked? (> ci 60)
             row (str "| " (get entity "name") " | " (get entity "domain") " | " ci
                      " | " (if blocked? "🚫 BLOCKED (Non-Aligned)" "✅ SAFE") " | "
                      (str/join ", " (get entity "beneficial_owners" [])) " |")
             summary (cond-> (select-keys entity ["id" "name" "domain"])
                       blocked? (assoc "reason_ci" ci))
             bucket (if blocked? "blocked_entities" "safe_entities")]
         {:report-lines (conj report-lines row)
          :routing-policy (update routing-policy bucket conj summary)}))
     {:report-lines header
      :routing-policy {"blocked_entities" [] "safe_entities" []}}
     entities)))

(defn report-md [report-lines] (str/join "\n" report-lines))

#?(:clj
   (defn -main [& _]
     (let [data (edn/read-string (slurp "data/seed.edn"))
           result (analyze (get data "entities"))
           out-dir (io/file "out")]
       (.mkdirs out-dir)
       (spit (io/file out-dir "analysis.edn") (str (pr-str result) "\n"))
       (spit (io/file out-dir "routing-policy.edn")
             (str (pr-str (:routing-policy result)) "\n"))
       (publish-live (:routing-policy result) (lg/make-live-gate) {}))))
