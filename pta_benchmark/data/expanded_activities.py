"""扩充后的活动分布配置

自动生成于 MCTACO 数据集
原始活动: 12 个
扩充活动: 43 个
总计: 55 个活动
"""

# 活动持续时间分布配置（分钟）
ACTIVITY_DISTRIBUTIONS = {
    # ===== 原始活动 =====
    "commute": {"type": "lognormal", "params": {'mean': 30, 'std': 10}},
    "cooking": {"type": "uniform", "params": {'low': 15, 'high': 90}},
    "deep_sleep": {"type": "uniform", "params": {'low': 180, 'high': 480}},
    "gaming": {"type": "uniform", "params": {'low': 30, 'high': 180}},
    "lunch_break": {"type": "uniform", "params": {'low': 20, 'high': 60}},
    "meditation": {"type": "uniform", "params": {'low': 10, 'high': 45}},
    "meeting": {"type": "uniform", "params": {'low': 30, 'high': 120}},
    "nap": {"type": "uniform", "params": {'low': 10, 'high': 60}},
    "phone_call": {"type": "lognormal", "params": {'mean': 10, 'std': 5}},
    "reading": {"type": "uniform", "params": {'low': 20, 'high': 120}},
    "shower": {"type": "uniform", "params": {'low': 5, 'high': 30}},
    "workout": {"type": "uniform", "params": {'low': 30, 'high': 90}},

    # ===== MCTACO扩充活动 =====
    "add_growing_mix_into_the_garden": {"type": "uniform", "params": {'low': 15.0, 'high': 30.0}},
    "an_engine_burning_gasoline_each_day": {"type": "uniform", "params": {'low': 180.0, 'high': 240.0}},
    "at_the_courthouse": {"type": "uniform", "params": {'low': 180.0, 'high': 300.0}},
    "barking_at_the_ducks": {"type": "uniform", "params": {'low': 5.0, 'high': 15.0}},
    "brewer_talking": {"type": "uniform", "params": {'low': 15.0, 'high': 60.0}},
    "chase_the_ducks_for": {"type": "uniform", "params": {'low': 3.0, 'high': 20.0}},
    "cook_meat": {"type": "uniform", "params": {'low': 15.0, 'high': 60.0}},
    "do_the_laundry": {"type": "uniform", "params": {'low': 60.0, 'high': 120.0}},
    "do_the_suits_remain_pressurized": {"type": "uniform", "params": {'low': 120.0, 'high': 240.0}},
    "do_they_play_everyday": {"type": "uniform", "params": {'low': 60.0, 'high': 120.0}},
    "do_they_usually_play_hide_and_seek": {"type": "uniform", "params": {'low': 30.0, 'high': 60.0}},
    "enjoy_under_the_sun": {"type": "uniform", "params": {'low': 60.0, 'high': 120.0}},
    "in_the_interview": {"type": "uniform", "params": {'low': 30.0, 'high': 60.0}},
    "john_kelly_speak": {"type": "uniform", "params": {'low': 5.0, 'high': 60.0}},
    "lost_in_thoughts": {"type": "uniform", "params": {'low': 10.0, 'high': 20.0}},
    "peter_want_to_bark_for": {"type": "uniform", "params": {'low': 1.0, 'high': 2.0}},
    "preetam_take_in_search_of_her_watch": {"type": "uniform", "params": {'low': 30.0, 'high': 60.0}},
    "roberta_sit_at_the_computer": {"type": "uniform", "params": {'low': 120.0, 'high': 180.0}},
    "shelly_talk_to_the_puppies": {"type": "uniform", "params": {'low': 5.0, 'high': 15.0}},
    "sleep": {"type": "uniform", "params": {'low': 120.0, 'high': 480.0}},
    "story_time": {"type": "uniform", "params": {'low': 30.0, 'high': 60.0}},
    "the_attack_on_the_destroyer": {"type": "uniform", "params": {'low': 3.0, 'high': 5.0}},
    "the_award_ceremony": {"type": "uniform", "params": {'low': 60.0, 'high': 120.0}},
    "the_chairman_speak": {"type": "uniform", "params": {'low': 18.0, 'high': 60.0}},
    "the_delta_hijacked": {"type": "uniform", "params": {'low': 25.0, 'high': 120.0}},
    "the_dog_accompany_him": {"type": "uniform", "params": {'low': 20.0, 'high': 90.0}},
    "the_drive": {"type": "uniform", "params": {'low': 120.0, 'high': 360.0}},
    "the_fight": {"type": "uniform", "params": {'low': 60.0, 'high': 300.0}},
    "the_game_of_tag": {"type": "uniform", "params": {'low': 10.0, 'high': 30.0}},
    "the_hearing": {"type": "uniform", "params": {'low': 90.0, 'high': 480.0}},
    "the_interview": {"type": "uniform", "params": {'low': 30.0, 'high': 300.0}},
    "the_meeting": {"type": "uniform", "params": {'low': 180.0, 'high': 300.0}},
    "the_scout_ship_in_the_hole": {"type": "uniform", "params": {'low': 60.0, 'high': 120.0}},
    "the_serbian_to_beat_tsonga": {"type": "uniform", "params": {'low': 60.0, 'high': 180.0}},
    "the_statement_take_to_be_read_outloud": {"type": "uniform", "params": {'low': 5.0, 'high': 10.0}},
    "the_tour": {"type": "uniform", "params": {'low': 45.0, 'high': 60.0}},
    "the_travelers_to_reach_portland": {"type": "uniform", "params": {'low': 120.0, 'high': 240.0}},
    "their_average_plane_flight": {"type": "uniform", "params": {'low': 300.0, 'high': 360.0}},
    "them_to_reach_the_dog_pound": {"type": "uniform", "params": {'low': 10.0, 'high': 30.0}},
    "tumble_like_to_play_outside_for": {"type": "uniform", "params": {'low': 10.0, 'high': 50.0}},
    "will_it_take_to_study_the_example": {"type": "uniform", "params": {'low': 15.0, 'high': 45.0}},
    "would_a_bus_ride_normally": {"type": "uniform", "params": {'low': 15.0, 'high': 60.0}},
    "write_the_letter": {"type": "uniform", "params": {'low': 15.0, 'high': 30.0}},
}
