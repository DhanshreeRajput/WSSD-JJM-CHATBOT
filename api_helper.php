<?php

class ChatbotAPI {
    private $base_url;
    private $session_id;

    public function __construct($base_url) {
        $this->base_url = $base_url;
        $this->session_id = $this->generateSessionId();
    }

    private function generateSessionId() {
        if (session_status() == PHP_SESSION_NONE) {
            session_start();
        }
        
        if (!isset($_SESSION['chatbot_session_id'])) {
            $_SESSION['chatbot_session_id'] = 'php_session_' . uniqid() . '_' . time();
        }
        
        return $_SESSION['chatbot_session_id'];
    }

    public function sendQuery($message, $language = 'en') {
        $url = $this->base_url . '/query/';
        $data = array(
            'input_text' => $message,
            'language' => $language,
            'session_id' => $this->session_id
        );

        $curl = curl_init();
        curl_setopt_array($curl, array(
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_ENCODING => '',
            CURLOPT_MAXREDIRS => 10,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
            CURLOPT_CUSTOMREQUEST => 'POST',
            CURLOPT_POSTFIELDS => json_encode($data),
            CURLOPT_HTTPHEADER => array(
                'Content-Type: application/json',
                'Accept: application/json'
            ),
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false
        ));

        $response = curl_exec($curl);
        $http_code = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        $error = curl_error($curl);
        curl_close($curl);

        if ($error) {
            return array(
                'success' => false,
                'error' => 'cURL Error: ' . $error
            );
        }

        if ($http_code !== 200) {
            return array(
                'success' => false,
                'error' => 'HTTP Error: ' . $http_code,
                'response' => $response
            );
        }

        $decoded_response = json_decode($response, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            return array(
                'success' => false,
                'error' => 'JSON Decode Error: ' . json_last_error_msg(),
                'raw_response' => $response
            );
        }

        return array(
            'success' => true,
            'data' => $decoded_response
        );
    }

    // NEW METHOD: Get simple grievance status
    public function getSimpleGrievanceStatus($grievance_id, $language = 'en') {
        $url = $this->base_url . '/grievance/status/';
        $data = array(
            'grievance_id' => $grievance_id,
            'language' => $language
        );

        $curl = curl_init();
        curl_setopt_array($curl, array(
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_ENCODING => '',
            CURLOPT_MAXREDIRS => 10,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
            CURLOPT_CUSTOMREQUEST => 'POST',
            CURLOPT_POSTFIELDS => json_encode($data),
            CURLOPT_HTTPHEADER => array(
                'Content-Type: application/json',
                'Accept: application/json'
            ),
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false
        ));

        $response = curl_exec($curl);
        $http_code = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        $error = curl_error($curl);
        curl_close($curl);

        if ($error) {
            return array(
                'success' => false,
                'error' => 'cURL Error: ' . $error
            );
        }

        if ($http_code !== 200) {
            return array(
                'success' => false,
                'error' => 'HTTP Error: ' . $http_code,
                'response' => $response
            );
        }

        $decoded_response = json_decode($response, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            return array(
                'success' => false,
                'error' => 'JSON Decode Error: ' . json_last_error_msg(),
                'raw_response' => $response
            );
        }

        return array(
            'success' => true,
            'data' => $decoded_response
        );
    }

    public function checkHealth() {
        $url = $this->base_url . '/health/';
        $curl = curl_init();
        curl_setopt_array($curl, array(
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10,
            CURLOPT_HTTPHEADER => array(
                'Accept: application/json'
            ),
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false
        ));

        $response = curl_exec($curl);
        $http_code = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        $error = curl_error($curl);
        curl_close($curl);

        if ($error || $http_code !== 200) {
            return false;
        }

        $decoded_response = json_decode($response, true);
        return $decoded_response && isset($decoded_response['status']) && $decoded_response['status'] === 'healthy';
    }

    public function getSuggestions($language = 'en') {
        $url = $this->base_url . '/suggestions/?language=' . urlencode($language);
        $curl = curl_init();
        curl_setopt_array($curl, array(
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10,
            CURLOPT_HTTPHEADER => array(
                'Accept: application/json'
            ),
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false
        ));

        $response = curl_exec($curl);
        $http_code = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        curl_close($curl);

        if ($http_code === 200) {
            $decoded_response = json_decode($response, true);
            if ($decoded_response && isset($decoded_response['suggestions'])) {
                return $decoded_response['suggestions'];
            }
        }

        return array();
    }
}
?>
