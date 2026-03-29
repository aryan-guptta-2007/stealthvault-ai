"""
StealthVault AI - AI Security Brain
Phase 1: Rule-based attack explanation engine.
Phase 4 will upgrade this to a fine-tuned LLM.

Answers three critical questions:
1. What attack is happening?
2. How dangerous is it?
3. What should I do?
"""

from app.models.alert import (
    BrainAnalysis,
    AttackType,
    RiskScore,
    Severity,
    ClassificationResult,
    AnomalyResult,
)


# Knowledge base: detailed info for each attack type
ATTACK_KNOWLEDGE = {
    AttackType.DDOS: {
        "name": "Volumetric Denial of Service (DDoS)",
        "description": "A massive traffic flood aimed at exhausting your network bandwidth and server processing power.",
        "what_is_happening": "🚨 **CRITICAL: WEAPONIZED TRAFFIC DETECTED.** Multiple sources are hitting your network with a synchronized flood. The attacker is trying to knock your services offline by overwhelming your CPU and bandwidth. This is not a random spike; it is a coordinated attempt to silence your infrastructure.",
        "how_to_stop": "1) Engage upstream scrubbing immediately. 2) Deploy SYN-ACK filtering. 3) Block the primary attacking subnet. 4) Scale your edge capacity if possible.",
        "technical_details": "Observed high-velocity packet bursts (SYN/UDP/ICMP). Traffic signature matches a volumetric botnet operation. PPS (Packets Per Second) is 10x above baseline.",
        "actions": [
            "Activate DDoS Mitigation Service (Cloudflare/AWS Shield)",
            "Enable SYN Cookies at the kernel level",
            "Drop all traffic from the detected attacking ASN",
            "Implement aggressive rate limiting on the edge firewall",
        ],
    },
    AttackType.PORT_SCAN: {
        "name": "Network Reconnaissance (Port Scan)",
        "description": "An attacker is systematically probing your network to find a 'way in'.",
        "what_is_happening": "🔍 **RECONNAISSANCE IN PROGRESS.** Someone is 'knocking on all your doors' to see which ones are unlocked. This is a classic precursor to a breach. They are mapping your services to find outdated software or vulnerable ports. If you don't block them now, an exploitation attempt will likely follow.",
        "how_to_stop": "1) Blacklist the scanner's IP immediately. 2) Close all non-essential ports. 3) Enable 'Port Knocking' or a VPN for administrative access.",
        "technical_details": "Detected sequential TCP SYN connection attempts across a wide range of ports. Pattern suggests an automated Nmap or ZMap scan.",
        "actions": [
            "Block the scanner's IP at the perimeter firewall",
            "Audit all open ports and disable non-critical services",
            "Set up a 'Honey Pot' port to trap further reconnaissance",
            "Review access logs for any follow-up exploit payloads",
        ],
    },
    AttackType.BRUTE_FORCE: {
        "name": "Active Brute Force / Credential Stuffing",
        "description": "Automated attempts to guess passwords and hijack user accounts.",
        "what_is_happening": "🔨 **BRUTE FORCE ATTACK.** An automated script is hammering your login forms with thousands of stolen credentials. They are betting on your users having weak or reused passwords. This is a direct attempt to seize control of high-privilege accounts.",
        "how_to_stop": "1) Force account lockouts. 2) Require Multi-Factor Authentication (MFA). 3) Block the source IP. 4) Use a Web Application Firewall (WAF) to challenge scripts.",
        "technical_details": "High-frequency POST requests to authentication endpoints. Use of common password dictionaries and 'Credential Stuffing' signatures detected.",
        "actions": [
            "Enable 2FA/MFA for all sensitive accounts",
            "Implement IP-based rate limiting on all /login routes",
            "Block the attacker's IP and associated proxy ranges",
            "Force a password reset for any account with ≥5 failed attempts",
        ],
    },
    AttackType.MALWARE: {
        "name": "Malware C2 (Command & Control) Beaconing",
        "description": "A compromised device on your network is talking to an external attacker.",
        "what_is_happening": "☣️ **INFECTION DETECTED.** One of your internal devices is 'calling home' to a malicious server. This is a clear indicator of a compromise. The malware is likely waiting for commands or preparing to exfiltrate your sensitive data. You have a spy inside your network.",
        "how_to_stop": "1) ISOLATE THE DEVICE IMMEDIATELY. 2) Kill the malicious process. 3) Block the external C2 domain. 4) Perform a deep forensic clean.",
        "technical_details": "Detected periodic, outbound heartbeat signals (beaconing). Payload size and timing match Command & Control communication profiles (Covenant, Metasploit, or Cobalt Strike).",
        "actions": [
            "Physically disconnect or VLAN-isolate the infected machine",
            "Block the destination IP/Domain at the global firewall level",
            "Perform RAM and disk forensics to find the persistence mechanism",
            "Identify the initial entry point (Phishing/Exploit) to prevent re-infection",
        ],
    },
    AttackType.SQL_INJECTION: {
        "name": "Database Exploitation (SQL Injection)",
        "description": "An attempt to steal, corrupt, or modify your database records.",
        "what_is_happening": "💉 **INJECTION ATTACK.** An attacker is trying to trick your application into leaking its database. They are sending malicious code into your input fields, hoping to bypass security and dump your user tables or administrator passwords. This is a direct threat to your data integrity.",
        "how_to_stop": "1) Use prepared statements (parameterized queries). 2) Sanitize all user input. 3) Use a WAF. 4) Block the attacker.",
        "technical_details": "Detected SQL-specific characters and keywords (`OR 1=1`, `UNION SELECT`, `SLEEP()`) in HTTP GET/POST parameters. Classic SQLi probe pattern.",
        "actions": [
            "Deploy WAF rules to filter common SQLi payloads",
            "Update application code to use parameterized database queries",
            "Review database logs for 'Information Schema' queries from this IP",
            "Block the attacker's IP and analyze their other requests",
        ],
    },
    AttackType.XSS: {
        "name": "Client-Side Hijacking (XSS)",
        "description": "Malicious code injection aimed at stealing user cookies and sessions.",
        "what_is_happening": "🎭 **SESSION HIJACKING ATTEMPT.** The attacker is trying to inject malicious JavaScript into your site. If successful, they can steal your users' session cookies and 'become' them. They are targeting your customers directly via your own application vulnerabilities.",
        "how_to_stop": "1) Sanitize and escape all output. 2) Set a strong Content Security Policy (CSP). 3) Always use HTTP-only cookies. 4) Block the attacker.",
        "technical_details": "Detected `<script>` tags, `onerror` handlers, or encoded JS payloads in request parameters. Pattern matches 'Reflected XSS' reconnaissance.",
        "actions": [
            "Enable a strict Content Security Policy (CSP)",
            "Escape all user-contributed content before rendering",
            "Set the `HttpOnly` flag on all session cookies",
            "Check for 'Stored XSS' in your database from this same source",
        ],
    },
    AttackType.NORMAL: {
        "name": "Legitimate Traffic",
        "description": "Standard, benign network activity.",
        "what_is_happening": "✅ **SYSTEM CLEAR.** This traffic matches normal behavioral baselines. No malicious intent or suspicious patterns detected. The network is operating as expected.",
        "how_to_stop": "No action required.",
        "technical_details": "Packet headers, timing, and payloads all fall within standard operating parameters.",
        "actions": ["Continue routine monitoring"],
    },
    AttackType.UNKNOWN: {
        "name": "Zero-Day / Anomalous Activity",
        "description": "Activity that looks suspicious but doesn't match any known signature.",
        "what_is_happening": "🕵️ **UNIDENTIFIED THREAT.** Our AI has flagged this traffic as highly unusual. It doesn't match any known attack, but its behavior is erratic compared to your typical network noise. This could be a zero-day exploit or a highly sophisticated, multi-stage attack in its early stages.",
        "how_to_stop": "1) Increase logging level. 2) Capture full packet data (PCAP). 3) Manually review the payload. 4) Block if risk score continues to climb.",
        "technical_details": "Isolation Forest flagged this as an outlier (Anomaly Score > 0.8). Behavioral characteristics are outside 99% of established normal traffic.",
        "actions": [
            "Manually inspect the raw packet payload for hidden commands",
            "Enable verbose logging for all associated connections",
            "Cross-reference this IP with global 'Tor' or 'Proxy' lists",
            "Consider a proactive temporary block of the source IP",
        ],
    },
}

SEVERITY_DESCRIPTIONS = {
    Severity.CRITICAL: "🔴 CRITICAL — Immediate action required. Active exploitation detected.",
    Severity.HIGH: "🟠 HIGH — Significant threat. Investigate and respond within 15 minutes.",
    Severity.MEDIUM: "🟡 MEDIUM — Moderate risk. Investigate within 1 hour.",
    Severity.LOW: "🟢 LOW — Minor concern. Review during next security check.",
}


class SecurityBrain:
    """
    AI Security Brain — explains attacks in human-readable language.
    
    Phase 1: Rule-based expert system with curated knowledge base.
    Phase 4: Will be upgraded to a fine-tuned LLM for dynamic responses.
    """

    def analyze(
        self,
        anomaly: AnomalyResult,
        classification: ClassificationResult,
        risk: RiskScore,
    ) -> BrainAnalysis:
        """
        Generate a comprehensive analysis of a detected threat.
        
        Returns human-readable explanation covering:
        - What is this attack?
        - How dangerous is it?
        - What should I do?
        """
        attack_type = classification.attack_type
        knowledge = ATTACK_KNOWLEDGE.get(attack_type, ATTACK_KNOWLEDGE[AttackType.UNKNOWN])

        danger_level = SEVERITY_DESCRIPTIONS.get(
            risk.severity,
            SEVERITY_DESCRIPTIONS[Severity.LOW],
        )

        # Enhance description with contextual details
        description = knowledge["description"]
        if anomaly.is_anomaly and attack_type == AttackType.NORMAL:
            description = (
                "⚠️ ANOMALY ALERT: Traffic flagged as anomalous by behavioral AI "
                "despite appearing normal to signature detection. This could indicate "
                "a novel attack technique or zero-day exploit. "
                + knowledge["description"]
            )

        return BrainAnalysis(
            attack_name=knowledge["name"],
            description=description,
            danger_level=danger_level,
            what_is_happening=knowledge["what_is_happening"],
            how_to_stop=knowledge["how_to_stop"],
            technical_details=knowledge["technical_details"],
            recommended_actions=knowledge["actions"],
        )


# Singleton
security_brain = SecurityBrain()
