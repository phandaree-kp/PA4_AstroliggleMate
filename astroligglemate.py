import streamlit as st
import openai
import pandas as pd
import json

#sidebar สำหรับใส่ API Key
user_api_key = st.sidebar.text_input("🔑 กรุณากรอก OpenAI API Key (ㅅ´ ˘ `)", type="password")

prompt_template = """
สมมติว่าคุณเป็นนักพยากรณ์ดวงที่เน้นคำทำนายแบบปั่น ขำขันสุด ๆ ฮาน้ำตาเล็ด 
คุณจะได้รับชื่อเพื่อน วันเกิด (วันในสัปดาห์) และนิสัยหรือพฤติกรรมเด่นของเพื่อน
สร้างคำทำนายสุดฮาใน 6 หมวดดังนี้:
1. การงาน
2. การเงิน
3. สุขภาพ
4. ความรัก
5. โชคลาภ
6. Lucky Item ประจำสัปดาห์ (คนที่เกิดในแต่ละวันจะได้ Lucky Item ต่างกันไปตามนิสัยหรือพฤติกรรมเด่นของเพื่อนที่ให้มา แต่สีของ item จะเหมือนกัน โดยคนเกิดวันจันทร์-สีเหลือง วันอังคาร-สีชมพู วันพุธ-สีเขียว วันพฤหัสบดี-สีส้ม วันศุกร์-สีฟ้า วันเสาร์-สีม่วง วันอาทิตย์-สีแดง)
จากนั้นส่งคำทำนายในรูปแบบ JSON array 
ตัวอย่างเช่น คุณได้รับชื่อเพื่อน "เจได" วันเกิด "วันอาทิตย์" นิสัยหรือพฤติกรรมเด่น "โสด สู้งาน ชอบเล่นเกม" คุณจะต้องสร้างคำทำนายและส่งคำทำนายในรูปแบบ JSON array ที่มีโครงสร้างดังต่อไปนี้:
[
    {"category": "การงาน", "prediction": "เจ้านายชมเชย! ( • ̀ω•́ )✧ แต่ไม่ได้ขึ้นเงินเดือน ╥‸╥"},
    {"category": "การเงิน", "prediction": "ได้เงินมาไวヾ(｡✪ω✪｡)ｼ💰 แต่หมดไปไวกว่า ∘ ∘ ∘ 💸( °ヮ° ) ?"},
    {"category": "สุขภาพ", "prediction": "ปวดหลังเพราะนั่งเล่นเกมยันเช้า ( TᗜT)🎮"},
    {"category": "ความรัก", "prediction": "คนโสดจะเจอคนถูกใจ (｡>\\<) แต่เขาดันมีแฟนแล้ว..."},
    {"category": "โชคลาภ", "prediction": "โชคลาภกำลังรอคุณอยู่ในมุมที่ไม่คาดคิด—อาจจะเป็นเงินในเครื่องซักผ้าที่ลืมหยิบออกจากกระเป๋ากางเกง!🧺🧼"},
    {"category": "Lucky Item ประจำสัปดาห์", "prediction": "แก้วกาแฟสีแดง เติมคาเฟอีนให้สมองพร้อมสู้งาน...หลังจากตบตีบอสในเกมมาทั้งคืน—☕(≖_≖ )"}
]
ไม่ต้องอธิบายเพิ่มเติม ส่งแค่ JSON array เท่านั้น
"""

#ส่วนหัวของแอป
st.title("ระบบพยากรณ์ดวงเพื่อนแบบปั่น 🔥🔮🌟")
st.write("กรอกข้อมูลเพื่อนของคุณ 👧🏻🧒🏻💞 (กรอกได้มากกว่า 1 คน สูงสุด 5 คน) เพื่อดูคำทำนายสุดฮา!")

#กรอกข้อมูลเพื่อนทีละคน (สูงสุด 5 คน)
friends_data = []
for i in range(1, 6):
    st.subheader(f"เพื่อนคนที่ {i} 🏃🏻‍♂️💨")
    friend_name = st.text_input(f"ชื่อเพื่อนคนที่ {i}", key=f"name_{i}")
    birthday = st.selectbox(
        f"วันเกิดคนที่ {i}", 
        ["วันอาทิตย์", "วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์"], 
        key=f"birthday_{i}"
    )
    behavior = st.text_input(
        f"นิสัยหรือพฤติกรรมเด่นของเพื่อนคนที่ {i} (ใส่ได้มากกว่า 1 ลักษณะ)", 
        placeholder="เช่น ชอบเบี้ยวนัด เมาแล้วเคยอุ้มหมากลับบ้าน ติดแฟน", 
        key=f"behavior_{i}"
    )
    if friend_name and birthday and behavior:
        friends_data.append({
            "name": friend_name,
            "birthday": birthday,
            "behavior": behavior
        })

#ตัวเลือกแปลภาษาเพิ่ม
translate_option = st.selectbox("🌍 เพิ่มคำแปลภาษาอื่นในคำทำนายไหม?", ["แค่ภาษาไทยก็พอแล้ว 😎", "English", "简体中文", "Español"])

#ปุ่มกดเพื่อขอคำทำนาย
if st.button("(๑'ᵕ'๑)⸝*🔮 ดูดวงง!"):
    if not user_api_key:
        st.error("กรุณาใส่ API Key ก่อนนะงั้ฟ! (ㅅ •᷄ ₃•᷅ )")
    elif not friends_data:
        st.error("กรุณากรอกข้อมูลเพื่อนให้ครบอย่างน้อย 1 คนน้า~ (｡- .•̀ )⟡˖ ࣪⋆")
    else:
        st.info("⏳ กำลังสร้างเรื่อง เอ้ย! สร้างคำทำนาย... โปรดรอสักครู่ ตรู้ดๆ")
        
        client = openai.OpenAI(api_key=user_api_key)
        results = []
        for friend in friends_data:
            name, birthday, behavior = friend["name"], friend["birthday"], friend["behavior"]
            messages = [
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": f"ชื่อ: {name}, วันเกิด: {birthday}, นิสัย: {behavior}"}
            ]

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages, 
                    temperature=0.9
                )
                horoscope_json = response.choices[0].message.content
                horoscope_list = json.loads(horoscope_json)

                for prediction in horoscope_list:
                    results.append({
                        "Name": name,
                        "Birthday": birthday,
                        "Behavior": behavior,
                        "Category": prediction["category"],
                        "Prediction": prediction["prediction"]
                    })

                #แปลภาษา (ถ้ามีการเลือก)
                if translate_option != "แค่ภาษาไทยก็พอแล้ว 😎":
                    for prediction in horoscope_list:
                        lang_mapping = {
                            "English": "English",
                            "简体中文": "Simplified Chinese",
                            "Español": "Spanish"
                        }

                        translation_prompt = f"""
                        สมมติว่าคุณเป็นนักแปลมืออาชีพที่มีความสามารถด้านการสื่อสารระดับสูง  
                        คุณจะได้รับคำทำนายดวงสุดฮา 1 รายการในภาษาไทย  
                        สิ่งที่คุณต้องทำมีดังนี้:
                        1. แปลคำทำนายให้มีความถูกต้อง แต่ยังคงรักษาอารมณ์ขันและโทนที่เป็นมิตรของต้นฉบับไว้
                        2. ทำให้คำแปลอ่านลื่นไหลและดูเป็นธรรมชาติในภาษาที่กำหนด
                        3. หลีกเลี่ยงการแปลที่ตรงตัวจนเกินไป ให้แปลในลักษณะที่เข้าใจง่ายและสนุกสนาน  

                        ตัวอย่างการแปล:
                        คำต้นฉบับ: "เจ้านายชมเชย! ( • ̀ω•́ )✧ แต่ไม่ได้ขึ้นเงินเดือน ╥‸╥"
                        ภาษาอังกฤษ: "Your boss gave you a compliment! ( • ̀ω•́ )✧ But nope, still no raise ╥‸╥"
                        ภาษาจีนตัวย่อ: "老板表扬了你！( • ̀ω•́ )✧ 可惜没给加薪 ╥‸╥"
                        ภาษาสเปน: "¡Tu jefe te elogió! ( • ̀ω•́ )✧ Pero no hay aumento de sueldo ╥‸╥"

                        ส่งเฉพาะคำแปลในภาษาที่กำหนดเท่านั้น: {lang_mapping[translate_option]}
                        คำทำนาย: {prediction['prediction']}
                        """

                        translation_response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": translation_prompt}]
                        )
                        prediction[f"Prediction_{translate_option}"] = translation_response.choices[0].message.content
                    results.append(prediction)


            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการประมวลผลคำทำนายสำหรับ {name}: {str(e)}")
                results.append({
                    "Name": name,
                    "Birthday": birthday,
                    "Behavior": behavior,
                    "Category": "Error",
                    "Prediction": str(e)
                })

        #สร้าง DataFrame
        df = pd.DataFrame(results)

        #แสดงผล
        st.subheader("📋 คำทำนายในรูปแบบตาราง 🔮")
        st.dataframe(df)
       

        #ดาวน์โหลด CSV
        csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 ดาวน์โหลดคำทำนาย (CSV)",
            data=csv,
            file_name="astroligglemate_result.csv",
            mime='text/csv'
        )
