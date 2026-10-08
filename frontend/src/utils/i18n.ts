import React, { createContext, useContext, useState, ReactNode } from 'react';

export type Language = 'en' | 'hi';

export const translations: Record<Language, Record<string, string>> = {
  en: {
    // Navigation
    'nav.title': 'OA-Sense AI',
    'nav.subtitle': 'AI-Assisted Early Osteoarthritis Screening',
    'nav.dashboard': 'Dashboard',
    'nav.patients': 'Patients',
    'nav.screenings': 'Screenings',
    'nav.newScreening': 'Start New Screening',
    'nav.reports': 'Reports',
    'nav.settings': 'Settings',
    'nav.logout': 'Logout',
    'nav.demoBadge': 'DEMO / RESEARCH PROTOTYPE',
    'nav.offline': 'Offline Mode',
    'nav.online': 'Connected',
    'nav.sync': 'Sync Pending',

    // Dashboard
    'dashboard.title': 'Community Healthcare Screening Dashboard',
    'dashboard.subtitle': 'Real-time biomechanical analysis & early OA risk stratification',
    'dashboard.totalPatients': 'Total Patients',
    'dashboard.screeningsToday': 'Screenings Today',
    'dashboard.highRisk': 'High Risk Cases',
    'dashboard.modRisk': 'Moderate Risk Cases',
    'dashboard.lowRisk': 'Low Risk Cases',
    'dashboard.riskDistribution': 'Risk Distribution',
    'dashboard.recentPatients': 'Recent Patients',
    'dashboard.startScreening': 'Start New Screening',
    'dashboard.patientId': 'Patient ID',
    'dashboard.name': 'Name',
    'dashboard.age': 'Age',
    'dashboard.lastScreening': 'Last Screening',
    'dashboard.riskLevel': 'Risk Level',
    'dashboard.action': 'Action',
    'dashboard.view': 'View',
    'dashboard.screen': 'Screen',

    // Patient Registration
    'patient.register': 'Register Patient',
    'patient.subtitle': 'Enter demographic information and clinical history',
    'patient.fullName': 'Full Name',
    'patient.ageLabel': 'Age',
    'patient.gender': 'Gender',
    'patient.male': 'Male',
    'patient.female': 'Female',
    'patient.other': 'Other',
    'patient.phone': 'Phone Number',
    'patient.location': 'Location / Camp Site',
    'patient.occupation': 'Occupation',
    'patient.activityLevel': 'Physical Activity Level',
    'patient.activitySedentary': 'Sedentary (Little or no exercise)',
    'patient.activityLight': 'Light (Gentle exercise/walking)',
    'patient.activityModerate': 'Moderate (Normal daily manual tasks)',
    'patient.activityHigh': 'High (Heavy physical/field labor)',
    'patient.riskFactors': 'Joint & Clinical Risk Factors',
    'patient.injury': 'Previous joint or knee injury',
    'patient.family': 'Family history of arthritis/joint disease',
    'patient.demanding': 'Physically demanding manual occupation',
    'patient.diffWalk': 'Noticeable difficulty walking long distances',
    'patient.diffStair': 'Difficulty climbing stairs',
    'patient.stiffness': 'Morning joint stiffness (> 30 mins)',
    'patient.saveOnly': 'Save Patient Record',
    'patient.saveAndStart': 'Save & Proceed to Screening',

    // Questionnaire
    'q.title': 'Pain & Mobility Questionnaire',
    'q.subtitle': 'Standardized functional assessment questionnaire',
    'q.q1': '1. Do you experience knee pain?',
    'q.q2': '2. Do you experience joint stiffness?',
    'q.q3': '3. Is walking difficult?',
    'q.q4': '4. Is climbing stairs difficult?',
    'q.q5': '5. Is standing for a long time difficult?',
    'q.q6': '6. Do you experience difficulty bending your knee?',
    'q.q7': '7. Does pain increase after physical activity?',
    'q.q8': '8. How would you rate your knee pain intensity? (0 = None, 10 = Severe)',
    'q.q9': '9. How would you rate your overall mobility? (0 = Immobility, 10 = Full Mobility)',
    'q.optNever': 'Never',
    'q.optRarely': 'Rarely',
    'q.optSometimes': 'Sometimes',
    'q.optOften': 'Often',
    'q.optAlways': 'Always',
    'q.next': 'Proceed to Camera Movement Test',

    // Movement Test
    'mov.title': 'Real-Time Camera Movement Analysis',
    'mov.safety': 'SAFETY NOTICE: Perform tests only if you can do so safely. Stop immediately if you feel pain, dizziness, or discomfort.',
    'mov.test1Title': 'Test 1: Knee Flexion / Extension',
    'mov.test1Desc': 'Bend your knee by bringing your heel toward your buttocks (or lift knee while bending). Keep hip steady so the knee joint angle bends.',
    'mov.test2Title': 'Test 2: Sit-to-Stand',
    'mov.test2Desc': 'Stand up from a chair and sit down safely and smoothly.',
    'mov.test3Title': 'Test 3: Walking Test',
    'mov.test3Desc': 'Walk naturally across the camera frame at a comfortable pace.',
    'mov.readyStatus': 'Status: Ready to start',
    'mov.readyInstruction': 'Position yourself properly, then click "Start Movement Test" to begin.',
    'mov.testCompleted': 'Completed',
    'mov.repsDetected': 'Reps Detected',
    'mov.repsNeeded': 'Reps Required',
    'mov.fps': 'FPS',
    'mov.poseDetected': 'Pose Detected',
    'mov.movementDetected': 'Movement Detected',
    'mov.leftKneeAngle': 'Left Knee Angle',
    'mov.rightKneeAngle': 'Right Knee Angle',
    'mov.status': 'Movement Status',
    'mov.postureScore': 'Posture Score',
    'mov.gaitSymmetry': 'Gait Symmetry',
    'mov.startTest': 'Start Movement Test',
    'mov.stopTest': 'Complete Test & Analyze',
    'mov.countdown': 'Get Ready...',

    // Results
    'result.title': 'OA Risk Screening Result',
    'result.screeningHeader': 'Preliminary Screening Assessment',
    'result.indicator': 'Risk Indicator',
    'result.confidence': 'Model Confidence',
    'result.questContrib': 'Questionnaire Contribution',
    'result.moveContrib': 'Movement Contribution',
    'result.topDrivers': 'Top Contributing Risk Indicators',
    'result.recommendations': 'Early Medical-Evaluation Guidance',
    'result.generatePdf': 'Generate PDF Report',
    'result.saveRecord': 'Save Patient Record',
    'result.newScreening': 'Start Another Screening',

    // Risk levels
    'risk.low': 'Low Risk',
    'risk.moderate': 'Moderate Risk',
    'risk.high': 'High Risk',

    // Disclaimer
    'disclaimer.banner': 'IMPORTANT: This application provides an AI-assisted screening assessment, NOT a medical diagnosis. Never rely solely on this automated tool for clinical decisions. Consultation with a qualified orthopedic specialist or physician is recommended.'
  },
  hi: {
    // Navigation
    'nav.title': 'ओए-सेंस एआई',
    'nav.subtitle': 'एआई-आधारित प्रारंभिक ऑस्टियोआर्थराइटिस जांच प्रणाली',
    'nav.dashboard': 'डैशबोर्ड',
    'nav.patients': 'मरीज़',
    'nav.screenings': 'स्क्रीनिंग',
    'nav.newScreening': 'नई स्क्रीनिंग शुरू करें',
    'nav.reports': 'रिपोर्ट्स',
    'nav.settings': 'सेटिंग्स',
    'nav.logout': 'लॉग आउट',
    'nav.demoBadge': 'डेमो / अनुसंधान प्रोटोटाइप',
    'nav.offline': 'ऑफ़लाइन मोड',
    'nav.online': 'इंटरनेट कनेक्टेड',
    'nav.sync': 'सिंक बाकी है',

    // Dashboard
    'dashboard.title': 'सामुदायिक स्वास्थ्य जांच डैशबोर्ड',
    'dashboard.subtitle': 'रीयल-टाइम बायोमैकेनिकल विश्लेषण और प्रारंभिक ओए जोखिम मूल्यांकन',
    'dashboard.totalPatients': 'कुल मरीज़',
    'dashboard.screeningsToday': 'आज की स्क्रीनिंग',
    'dashboard.highRisk': 'उच्च जोखिम मामले',
    'dashboard.modRisk': 'मध्यम जोखिम मामले',
    'dashboard.lowRisk': 'कम जोखिम मामले',
    'dashboard.riskDistribution': 'जोखिम वितरण',
    'dashboard.recentPatients': 'हाल के मरीज़',
    'dashboard.startScreening': 'नई स्क्रीनिंग शुरू करें',
    'dashboard.patientId': 'मरीज़ आईडी',
    'dashboard.name': 'नाम',
    'dashboard.age': 'उम्र',
    'dashboard.lastScreening': 'पिछली स्क्रीनिंग',
    'dashboard.riskLevel': 'जोखिम स्तर',
    'dashboard.action': 'कार्रवाई',
    'dashboard.view': 'देखें',
    'dashboard.screen': 'स्क्रीन करें',

    // Patient Registration
    'patient.register': 'मरीज़ का पंजीकरण करें',
    'patient.subtitle': 'मरीज़ की बुनियादी जानकारी और स्वास्थ्य इतिहास भरें',
    'patient.fullName': 'पूरा नाम',
    'patient.ageLabel': 'उम्र',
    'patient.gender': 'लिंग',
    'patient.male': 'पुरुष',
    'patient.female': 'महिला',
    'patient.other': 'अन्य',
    'patient.phone': 'फ़ोन नंबर',
    'patient.location': 'स्थान / स्वास्थ्य केंद्र',
    'patient.occupation': 'व्यवसाय',
    'patient.activityLevel': 'शारीरिक गतिविधि स्तर',
    'patient.activitySedentary': 'निष्क्रिय (कम या कोई व्यायाम नहीं)',
    'patient.activityLight': 'हल्का (सामान्य टहलना)',
    'patient.activityModerate': 'मध्यम (नियमित शारीरिक कार्य)',
    'patient.activityHigh': 'उच्च (कड़ा शारीरिक श्रम)',
    'patient.riskFactors': 'जोड़ों से संबंधित जोखिम कारक',
    'patient.injury': 'घुटने या जोड़ में पुरानी चोट',
    'patient.family': 'परिवार में गठिया/जोड़ों के दर्द का इतिहास',
    'patient.demanding': 'अधिक शारीरिक श्रम वाला काम',
    'patient.diffWalk': 'चलने-फिरने में परेशानी',
    'patient.diffStair': 'सीढ़ियां चढ़ने-उतरने में कठिनाई',
    'patient.stiffness': 'सुबह जोड़ों में अकड़न (> 30 मिनट)',
    'patient.saveOnly': 'मरीज़ रिकॉर्ड सहेजें',
    'patient.saveAndStart': 'सहेजें और स्क्रीनिंग शुरू करें',

    // Questionnaire
    'q.title': 'दर्द और गतिशीलता प्रश्नावली',
    'q.subtitle': 'मानकीकृत कार्यात्मक लक्षण मूल्यांकन',
    'q.q1': '1. क्या आपको घुटने में दर्द महसूस होता है?',
    'q.q2': '2. क्या आपको जोड़ों में अकड़न महसूस होती है?',
    'q.q3': '3. क्या चलने में कठिनाई होती है?',
    'q.q4': '4. क्या सीढ़ियां चढ़ने में परेशानी होती है?',
    'q.q5': '5. क्या अधिक देर खड़े रहने में समस्या होती है?',
    'q.q6': '6. क्या घुटना मोड़ने में परेशानी होती है?',
    'q.q7': '7. क्या शारीरिक गतिविधि के बाद दर्द बढ़ जाता है?',
    'q.q8': '8. अपने घुटने के दर्द की तीव्रता बताएं (0 = बिल्कुल नहीं, 10 = अत्यधिक)',
    'q.q9': '9. अपनी समग्र गतिशीलता बताएं (0 = चलने में असमर्थ, 10 = पूर्ण स्वस्थ)',
    'q.optNever': 'कभी नहीं',
    'q.optRarely': 'शायद ही कभी',
    'q.optSometimes': 'कभी-कभार',
    'q.optOften': 'अक्सर',
    'q.optAlways': 'हमेशा',
    'q.next': 'कैमरा मूवमेंट टेस्ट पर जाएं',

    // Movement Test
    'mov.title': 'रीयल-टाइम कैमरा मूवमेंट विश्लेषण',
    'mov.safety': 'सुरक्षा चेतावनी: यह परीक्षण केवल तभी करें जब आप सुरक्षित महसूस करें। दर्द या चक्कर आने पर तुरंत रुक जाएं।',
    'mov.test1Title': 'टेस्ट 1: घुटना मोड़ना और सीधा करना',
    'mov.test1Desc': 'धीरे-धीरे अपने घुटने को मोड़ें और सीधा करें।',
    'mov.test2Title': 'टेस्ट 2: उठना और बैठना',
    'mov.test2Desc': 'कुर्सी से सुरक्षित रूप से उठें और वापस बैठें।',
    'mov.test3Title': 'टेस्ट 3: चलने का परीक्षण',
    'mov.test3Desc': 'कैमरे के सामने सामान्य गति से चलें।',
    'mov.readyStatus': 'स्थिति: शुरू करने के लिए तैयार',
    'mov.readyInstruction': 'सही स्थिति में आएं, फिर "मूवमेंट टेस्ट शुरू करें" दबाएं।',
    'mov.testCompleted': 'पूर्ण हुआ',
    'mov.repsDetected': 'दर्ज पुनरावृत्तियाँ',
    'mov.repsNeeded': 'आवश्यक पुनरावृत्तियाँ',
    'mov.fps': 'एफ़पीएस',
    'mov.poseDetected': 'मुद्रा पहचानी गई',
    'mov.movementDetected': 'गतिविधि दर्ज',
    'mov.leftKneeAngle': 'बायां घुटना कोण',
    'mov.rightKneeAngle': 'दायां घुटना कोण',
    'mov.status': 'मूवमेंट स्थिति',
    'mov.postureScore': 'पोस्चर स्कोर',
    'mov.gaitSymmetry': 'चाल समरूपता (गेट सिमेट्री)',
    'mov.startTest': 'मूवमेंट टेस्ट शुरू करें',
    'mov.stopTest': 'परीक्षण समाप्त करें और विश्लेषण देखें',
    'mov.countdown': 'तैयार हो जाएं...',

    // Results
    'result.title': 'ओए जोखिम स्क्रीनिंग परिणाम',
    'result.screeningHeader': 'प्रारंभिक जोखिम मूल्यांकन रिपोर्ट',
    'result.indicator': 'जोखिम सूचक',
    'result.confidence': 'मॉडल विश्वसनीयता',
    'result.questContrib': 'प्रश्नावली का प्रभाव',
    'result.moveContrib': 'मूवमेंट का प्रभाव',
    'result.topDrivers': 'मुख्य जोखिम कारक',
    'result.recommendations': 'चिकित्सीय परामर्श सुझाव',
    'result.generatePdf': 'पीडीएफ़ रिपोर्ट बनाएं',
    'result.saveRecord': 'मरीज़ रिकॉर्ड सहेजें',
    'result.newScreening': 'नई स्क्रीनिंग शुरू करें',

    // Risk levels
    'risk.low': 'कम जोखिम (Low Risk)',
    'risk.moderate': 'मध्यम जोखिम (Moderate Risk)',
    'risk.high': 'उच्च जोखिम (High Risk)',

    // Disclaimer
    'disclaimer.banner': 'महत्वपूर्ण सूचना: यह प्रणाली एआई-सहायता प्राप्त प्रारंभिक स्क्रीनिंग है, कोई अंतिम चिकित्सा निदान नहीं। किसी योग्य आर्थोपेडिक चिकित्सक से परामर्श अवश्य लें।'
  }
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType>({
  language: 'en',
  setLanguage: () => {},
  t: (k) => k
});

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>('en');

  const t = (key: string): string => {
    return translations[language][key] || translations['en'][key] || key;
  };

  return (
    React.createElement(LanguageContext.Provider, { value: { language, setLanguage, t } }, children)
  );
};

export const useTranslation = () => useContext(LanguageContext);
