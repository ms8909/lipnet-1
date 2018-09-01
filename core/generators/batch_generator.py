import numpy as np

from common.files import get_file_name
from core.helpers.video import get_video_data_from_file
from keras.utils import Sequence


class BatchGenerator(Sequence):

	def __init__(self, video_paths: list, align_hash: dict, batch_size: int):
		self.video_paths = video_paths
		self.align_hash  = align_hash
		self.batch_size  = batch_size

		self.videos_len = len(self.video_paths)
		# self.videos_per_batch = self.batch_size
		self.videos_per_batch = int(np.ceil(self.batch_size / 2))

		self.generator_steps = int(np.ceil(self.videos_len / self.videos_per_batch))


	def __len__(self) -> int:
		return self.generator_steps


	def __getitem__(self, idx: int) -> (dict, dict):
		split_start = idx * self.videos_per_batch
		split_end   = split_start + self.videos_per_batch

		if split_end > self.videos_len:
			split_end = self.videos_len

		videos_batch = self.video_paths[split_start:split_end]
		videos_taken = len(videos_batch)

		videos_to_augment = self.batch_size - videos_taken

		x_data = []
		y_data = []
		input_length = []
		label_length = []
		sentences = []

		for path in videos_batch:
			video_data, label, label_len, sentence = self.get_data_from_path(path)

			x_data.append(video_data)
			y_data.append(label)
			label_length.append(label_len)
			input_length.append(len(video_data))
			sentences.append(sentence)

			# Temporarily disabling video augmentation
			if videos_to_augment > 0:
				videos_to_augment -= 1

				f_video_data = self.flip_video(video_data)

				x_data.append(f_video_data)
				y_data.append(label)
				label_length.append(label_len)
				input_length.append(len(video_data))
				sentences.append(sentence)
		
		x_data = np.array(x_data)
		# Batch standardization appears to be causing more problems than improvements.
		# x_data = (x_data - np.mean(x_data)) / np.std(x_data)

		y_data = np.array(y_data)
		input_length = np.array(input_length)
		label_length = np.array(label_length)
		sentences    = np.array(sentences)

		inputs = {
			'input'       : x_data,
			'labels'      : y_data,
			'input_length': input_length,
			'label_length': label_length,
			'sentences'  : sentences
		}

		real_batch_size = len(x_data)
		outputs = { 'ctc': np.zeros([real_batch_size]) } # dummy data for dummy loss function

		return inputs, outputs


	def get_data_from_path(self, path: str) -> (np.ndarray, np.ndarray, int, str):
		video_data = get_video_data_from_file(path)
		align_data = self.align_hash[get_file_name(path)]

		return video_data, align_data.padded_label, align_data.label_length, align_data.sentence


	def flip_frame(self, frame: np.ndarray) -> np.ndarray:
		return np.fliplr(frame)


	def flip_video(self, video_data: np.ndarray) -> np.ndarray:
		return np.array([self.flip_frame(f) for f in video_data])